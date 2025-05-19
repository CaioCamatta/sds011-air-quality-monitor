#!/usr/bin/python3
# coding=utf-8
import serial, time, argparse
from prometheus_client import start_http_server, Gauge
import threading

# Command definitions for the SDS011 sensor
CMD_MODE = 2
CMD_QUERY_DATA = 4
CMD_DEVICE_ID = 5
CMD_SLEEP = 6
CMD_FIRMWARE = 7
CMD_WORKING_PERIOD = 8
MODE_ACTIVE = 0
MODE_QUERY = 1
PERIOD_CONTINUOUS = 0

# Create Prometheus metrics
PM25_GAUGE = Gauge('sds011_pm25', 'PM2.5 particulate matter in μg/m³')
PM10_GAUGE = Gauge('sds011_pm10', 'PM10 particulate matter in μg/m³')

def dump(d, prefix=''):
    """Print byte data in hex format for debugging"""
    print(prefix + ' '.join('{:02x}'.format(b) for b in d))

def construct_command(cmd, data=[], debug=False):
    """Construct a command packet to send to the SDS011 sensor"""
    assert len(data) <= 12
    data += [0,]*(12-len(data))  # Pad with zeros to 12 bytes
    checksum = (sum(data)+cmd-2)%256  # Calculate checksum per sensor protocol
    
    # Build the command packet: header + command + data + ID + checksum + tail
    ret = bytearray([0xaa, 0xb4, cmd])
    ret.extend(data)
    ret.extend([0xff, 0xff, checksum, 0xab])

    if debug:
        dump(ret, '> ')
    return ret

def process_data(d, debug=False, verbose=True):
    """Process the data returned from the sensor"""
    if len(d) < 10:
        if verbose:
            print(f"Warning: Expected 10 bytes for data, got {len(d)}")
            dump(d, 'Data: ')
        return None
        
    try:
        # Extract PM2.5 and PM10 values according to the SDS011 protocol
        pm25_low = d[2]
        pm25_high = d[3]
        pm10_low = d[4]
        pm10_high = d[5]
        
        # Calculate real values: data is sent in 0.1 μg/m³ units
        pm25 = (pm25_high * 256 + pm25_low) / 10.0
        pm10 = (pm10_high * 256 + pm10_low) / 10.0
        
        if debug:
            print(f"PM2.5: {pm25_low},{pm25_high} -> {pm25:.1f} μg/m³")
            print(f"PM10: {pm10_low},{pm10_high} -> {pm10:.1f} μg/m³")
        
        return [pm25, pm10]
    except Exception as e:
        if verbose:
            print(f"Error processing data: {e}")
            dump(d, 'Raw data: ')
        return None

def read_response(debug=False, verbose=True):
    """Read and validate the response from the sensor"""
    try:
        # Look for the start byte (0xAA)
        byte = 0
        attempts = 0
        max_attempts = 100
        
        while byte != 0xaa and attempts < max_attempts:
            byte_str = ser.read(size=1)
            if not byte_str:
                if verbose:
                    print("No data received from sensor")
                time.sleep(0.1)
                attempts += 1
                continue
                
            byte = byte_str[0]
            attempts += 1

        if attempts >= max_attempts:
            if verbose:
                print("Failed to get proper response after max attempts")
            return bytearray()
            
        # Read the rest of the response (9 more bytes)
        d = ser.read(size=9)
        if debug:
            full_response = bytearray([byte]) + d
            dump(full_response, '< ')
        return bytearray([byte]) + d
    except Exception as e:
        if verbose:
            print(f"Exception in read_response: {e}")
        return bytearray()

def cmd_set_mode(mode=MODE_QUERY, debug=False, verbose=True):
    """Set the reporting mode of the sensor"""
    ser.write(construct_command(CMD_MODE, [0x1, mode], debug))
    read_response(debug, verbose)

def cmd_query_data(debug=False, verbose=True):
    """Request a new measurement from the sensor"""
    ser.write(construct_command(CMD_QUERY_DATA, debug=debug))
    d = read_response(debug, verbose)
    values = None
    if len(d) >= 10 and d[1] == 0xc0:  # Valid response has 0xC0 as command byte
        values = process_data(d, debug, verbose)
    return values

def cmd_set_sleep(sleep, debug=False, verbose=True):
    """Set the sensor to sleep mode or wake it up"""
    mode = 0 if sleep else 1  # 0 = sleep, 1 = wake
    ser.write(construct_command(CMD_SLEEP, [0x1, mode], debug))
    read_response(debug, verbose)

def cmd_set_working_period(period, debug=False, verbose=True):
    """Set the working period of the sensor"""
    ser.write(construct_command(CMD_WORKING_PERIOD, [0x1, period], debug))
    read_response(debug, verbose)

def start_prometheus_server(port=8000):
    """Start the Prometheus metrics HTTP server"""
    start_http_server(port)
    print(f"Prometheus metrics server started on port {port}")

if __name__ == "__main__":
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='SDS011 Air Quality Monitor')
    parser.add_argument('--no-sleep', action='store_true', help='Disable sleep mode (continuous measurements)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--quiet', action='store_true', help='Reduce verbosity (only print averages)')
    parser.add_argument('--port', type=int, default=8000, help='Prometheus metrics server port')
    parser.add_argument('--prometheus', action='store_true', help='Enable Prometheus metrics publishing')
    args = parser.parse_args()
    
    # Set variables from arguments
    DEBUG = args.debug
    VERBOSE = not args.quiet
    SLEEP_ENABLED = not args.no_sleep
    PROMETHEUS_ENABLED = args.prometheus
    
    # Start Prometheus metrics server if enabled
    if PROMETHEUS_ENABLED:
        start_prometheus_server(args.port)
        if VERBOSE:
            print(f"Prometheus metrics available at http://localhost:{args.port}/metrics")
    
    # Setup serial connection
    ser = serial.Serial()
    ser.port = "/dev/ttyUSB0"
    ser.baudrate = 9600
    
    ser.open()
    ser.flushInput()
    
    if VERBOSE:
        print("Starting air quality monitoring...")
        print("Settings:")
        print(f"  Debug mode: {'Enabled' if DEBUG else 'Disabled'}")
        print(f"  Sleep mode: {'Enabled' if SLEEP_ENABLED else 'Disabled'}")
        print(f"  Verbosity: {'Full' if VERBOSE else 'Minimal'}")
        print(f"  Prometheus metrics: {'Enabled' if PROMETHEUS_ENABLED else 'Disabled'}")
        if PROMETHEUS_ENABLED:
            print(f"  Prometheus port: {args.port}")
        print("Setting up sensor...")
    
    try:
        # Initialize the sensor
        cmd_set_sleep(0, DEBUG, VERBOSE)  # Wake up the sensor
        cmd_set_working_period(PERIOD_CONTINUOUS, DEBUG, VERBOSE)  # Set to continuous measurement
        cmd_set_mode(MODE_QUERY, DEBUG, VERBOSE)  # Set to query mode
        
        if VERBOSE:
            print("Starting main loop...")
        
        while True:
            cmd_set_sleep(0, DEBUG, VERBOSE)  # Ensure the sensor is awake
            valid_readings = 0
            pm25_sum = 0
            pm10_sum = 0
            
            # Take multiple readings to create a stable average
            readings_per_cycle = 15
            
            for t in range(readings_per_cycle):
                values = cmd_query_data(DEBUG, VERBOSE)
                if values is not None and len(values) == 2:
                    if VERBOSE:
                        print(f"PM2.5: {values[0]:.1f} μg/m³, PM10: {values[1]:.1f} μg/m³")
                    valid_readings += 1
                    pm25_sum += values[0]
                    pm10_sum += values[1]
                else:
                    if VERBOSE:
                        print("Invalid reading received")
                time.sleep(2)  # Wait between readings
            
            # Calculate and report averages
            if valid_readings > 0:
                pm25_avg = pm25_sum / valid_readings
                pm10_avg = pm10_sum / valid_readings
                
                # Update Prometheus metrics if enabled
                if PROMETHEUS_ENABLED:
                    PM25_GAUGE.set(pm25_avg)
                    PM10_GAUGE.set(pm10_avg)
                
                # Always print averages, even in quiet mode
                print(f"AVERAGE: PM2.5: {pm25_avg:.1f} μg/m³, PM10: {pm10_avg:.1f} μg/m³ (from {valid_readings} readings)")
                
                # Handle sleep mode based on flag
                if SLEEP_ENABLED:
                    if VERBOSE:
                        print("Going to sleep for 1 min...")
                    cmd_set_sleep(1, DEBUG, VERBOSE)  # Put sensor to sleep
                    time.sleep(60)  # Sleep for 1 minute
                else:
                    if VERBOSE:
                        print("Continuing measurements (sleep disabled)...")
                    time.sleep(2)  # Just pause briefly before the next cycle
            else:
                if VERBOSE:
                    print("No valid readings in this cycle, retrying...")
                time.sleep(5)  # Short retry delay
                
    except KeyboardInterrupt:
        if VERBOSE:
            print("Program stopped by user")
    except Exception as e:
        if VERBOSE:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
    finally:
        # Clean up before exit
        if VERBOSE:
            print("Closing serial port")
        ser.close()
