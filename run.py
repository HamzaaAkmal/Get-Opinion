#!/usr/bin/env python3
"""
Simple runner script for the YouTube Scrapping Application

This script provides a convenient way to start the application
with common environment configurations.

Usage:
    python run.py              # Start in development mode
    python run.py --prod       # Start in production mode
    python run.py --test       # Start in testing mode
    python run.py --help       # Show help message
"""

import sys
import argparse
from main import main


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='YouTube Scrapping Application Runner',
        epilog='Example: python run.py --env production --host 0.0.0.0 --port 8080'
    )
    
    parser.add_argument(
        '--env', '--environment',
        choices=['development', 'production', 'testing'],
        default='development',
        help='Environment configuration to use (default: development)'
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind the server to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind the server to (default: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (overrides environment setting)'
    )
    
    parser.add_argument(
        '--no-debug',
        action='store_true',
        help='Disable debug mode (overrides environment setting)'
    )
    
    # Convenience flags
    parser.add_argument(
        '--prod', '--production',
        action='store_const',
        const='production',
        dest='env',
        help='Shortcut for --env production'
    )
    
    parser.add_argument(
        '--test', '--testing',
        action='store_const',
        const='testing',
        dest='env',
        help='Shortcut for --env testing'
    )
    
    parser.add_argument(
        '--dev', '--development',
        action='store_const',
        const='development',
        dest='env',
        help='Shortcut for --env development (default)'
    )
    
    return parser.parse_args()


def setup_environment(args):
    """Setup environment variables based on arguments"""
    import os
    
    # Set environment
    os.environ['FLASK_ENV'] = args.env
    
    # Set host and port
    os.environ['FLASK_HOST'] = args.host
    os.environ['FLASK_PORT'] = str(args.port)
    
    # Handle debug mode
    if args.debug:
        os.environ['FLASK_DEBUG'] = 'True'
    elif args.no_debug:
        os.environ['FLASK_DEBUG'] = 'False'
    elif args.env == 'production':
        os.environ['FLASK_DEBUG'] = 'False'
    else:
        # Default to True for development and testing
        os.environ['FLASK_DEBUG'] = 'True'


def main_runner():
    """Main runner function"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Setup environment based on arguments
        setup_environment(args)
        
        # Print startup message
        print(f"🚀 Starting YouTube Scrapping Application...")
        print(f"📊 Environment: {args.env}")
        print(f"🌍 Server: http://{args.host}:{args.port}")
        print(f"🐛 Debug: {'On' if args.debug or (args.env != 'production' and not args.no_debug) else 'Off'}")
        print("-" * 50)
        
        # Start the application
        main()
        
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main_runner()