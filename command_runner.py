import subprocess
import sys
import os
import time
from datetime import datetime
import logging
import multiprocessing
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=os.path.join('logs', f'command_runner_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Log script start
logging.info("Command Runner Script Started")
logging.info(f"Current working directory: {os.getcwd()}")

def run_command(command: str) -> Tuple[str, bool]:
    """Run a command in the terminal and return its output and success status."""
    try:
        print(f"\nExecuting command: {command}")
        print("-" * 50)
        
        # Run the command and capture output
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Read output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # Get the return code
        return_code = process.poll()
        
        # Log the command execution
        logging.info(f"Command executed: {command}")
        logging.info(f"Return code: {return_code}")
        
        return f"Command completed with return code: {return_code}", return_code == 0
    except Exception as e:
        error_msg = f"Error executing command: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        return error_msg, False

def run_recursive_command(command: str, start_num: int, end_num: int, delay: int = 0, parallel: bool = False, max_parallel: int = None) -> None:
    """Run a command multiple times, replacing {N} with sequential numbers."""
    print(f"\nRunning command recursively from {start_num} to {end_num}")
    print(f"Command template: {command}")
    print(f"Delay between commands: {delay} seconds")
    print(f"Parallel execution: {'Enabled' if parallel else 'Disabled'}")
    
    if parallel:
        # Generate all commands
        commands = [command.replace("{N}", str(num)) for num in range(start_num, end_num + 1)]
        
        # Set max parallel processes
        if max_parallel is None:
            max_parallel = multiprocessing.cpu_count()
        
        print(f"Running {len(commands)} commands in parallel (max {max_parallel} at a time)")
        
        # Create a pool of workers
        with multiprocessing.Pool(processes=max_parallel) as pool:
            # Run all commands in parallel
            results = pool.map(run_command, commands)
        
        # Print summary
        print("\nParallel execution completed!")
        successful = sum(1 for _, success in results if success)
        failed = len(commands) - successful
        print(f"Successfully completed: {successful}")
        print(f"Failed: {failed}")
    
    else:
        # Sequential execution
        for num in range(start_num, end_num + 1):
            # Replace {N} with the current number
            current_command = command.replace("{N}", str(num))
            
            # Run the command
            output, success = run_command(current_command)
            
            if not success:
                print(f"Command failed for number {num}")
                return
            
            # Wait before running the next command
            if num < end_num and delay > 0:
                print(f"\nWaiting {delay} seconds before next command...")
                time.sleep(delay)

def main():
    parser = argparse.ArgumentParser(description='Run commands recursively and in parallel')
    parser.add_argument('--recursive', action='store_true', required=True,
                      help='Enable recursive execution')
    parser.add_argument('--parallel', action='store_true',
                      help='Enable parallel execution')
    parser.add_argument('command', help='Command template with {N} placeholder')
    parser.add_argument('start_num', type=int, help='Starting number')
    parser.add_argument('end_num', type=int, help='Ending number')
    parser.add_argument('delay', type=float, nargs='?', default=0,
                      help='Delay between commands in seconds')
    parser.add_argument('max_parallel', type=int, nargs='?', default=3,
                      help='Maximum number of parallel processes')
    
    args = parser.parse_args()
    
    # Log command line arguments
    logging.info("Command line arguments:")
    logging.info(f"Command template: {args.command}")
    logging.info(f"Start number: {args.start_num}")
    logging.info(f"End number: {args.end_num}")
    logging.info(f"Delay: {args.delay}")
    logging.info(f"Parallel: {args.parallel}")
    if args.parallel:
        logging.info(f"Max parallel: {args.max_parallel}")
    
    if args.recursive:
        if args.parallel:
            run_recursive_command(args.command, args.start_num, args.end_num, args.delay, True, args.max_parallel)
        else:
            run_recursive_command(args.command, args.start_num, args.end_num, args.delay, False)
    else:
        print("Error: Invalid mode. Use --recursive for recursive execution.")
        sys.exit(1)

    logging.info("Script completed successfully")

if __name__ == "__main__":
    main() 