# Web Image Scraper and Command Runner

This repository contains Python scripts for web scraping and command automation:

1. `image_scraper.py`: A web scraping tool for downloading images from websites
2. `command_runner.py`: A command automation tool for running commands recursively and in parallel

## Requirements

```bash
pip install -r requirements.txt
```

## 1. Image Scraper (`image_scraper.py`)

A powerful web scraping tool that downloads images from websites with support for various image formats and lazy-loaded images.

### Features

- Downloads images from any website
- Supports multiple image formats (jpg, jpeg, png, gif, bmp, webp, svg)
- Handles lazy-loaded images
- Extracts images from JSON data
- Creates chapter-specific folders for organized downloads
- Real-time progress tracking
- Detailed error handling and logging
- Supports data URLs and base64 encoded images
- Custom user agent and headers for better compatibility

### Usage

```bash
python image_scraper.py <website_url> [extension]
```

### Parameters

- `website_url`: The URL of the webpage containing images
- `extension`: (Optional) Filter images by extension (e.g., 'webp', 'jpg')

### Examples

1. Download all images from a webpage:
```bash
python image_scraper.py https://example.com
```

2. Download only webp images:
```bash
python image_scraper.py https://example.com webp
```

3. Download images from a manga chapter:
```bash
python image_scraper.py https://example.com/manga/chapter-1/ webp
```

### Output Structure

```
downloaded_images/
    run_DD-MM-YYYY_HH-MM-SS_chapter_X/
        image1.webp
        image2.webp
        ...
```

## 2. Command Runner (`command_runner.py`)

A flexible command automation tool that can run commands recursively and in parallel.

### Features

- Run commands recursively with changing parameters
- Support for parallel execution
- Configurable delay between commands
- Real-time output display
- Detailed logging
- Success/failure tracking

### Usage

1. Sequential Execution:
```bash
python command_runner.py --recursive 'command with {N}' <start_number> <end_number> [delay]
```

2. Parallel Execution:
```bash
python command_runner.py --recursive --parallel 'command with {N}' <start_number> <end_number> [delay] [max_parallel]
```

### Parameters

- `--recursive`: Required for recursive execution
- `--parallel`: Optional flag to enable parallel execution
- `command with {N}`: The command template where {N} will be replaced with numbers
- `start_number`: First number to use
- `end_number`: Last number to use
- `delay`: Optional delay between commands (in seconds)
- `max_parallel`: Optional maximum number of parallel processes (only used with --parallel)

### Examples

1. Sequential execution (one chapter at a time):
```bash
python command_runner.py --recursive "python image_scraper.py https://example.com/chapter-{N}/ webp" 1 5 2
```

2. Parallel execution (multiple chapters at once):
```bash
python command_runner.py --recursive --parallel "python image_scraper.py https://example.com/chapter-{N}/ webp" 1 5 2 3
```

### Directory Structure

```
project_root/
├── downloaded_images/        # Images downloaded by image_scraper.py
└── logs/                     # Log files for all scripts
```

## Combined Usage Example

To download multiple chapters of a manga in parallel:

```bash
python command_runner.py --recursive --parallel "python image_scraper.py https://example.com/manga/chapter-{N}/ webp" 1 10 2 3
```

This will:
1. Download chapters 1 through 10
2. Run 3 chapters simultaneously
3. Wait 2 seconds between starting new batches
4. Save images in chapter-specific folders

## Error Handling

All scripts include comprehensive error handling:
- Network errors
- Invalid URLs
- File system errors
- Command execution errors
- Timeout handling

## Logging

All scripts save their logs in the `logs` directory:
- `image_scraper_YYYYMMDD_HHMMSS.log`
- `command_runner_YYYYMMDD_HHMMSS.log`

## Notes

- Always check the website's robots.txt and terms of service before scraping
- Some websites may block automated requests
- Consider adding delays between requests to avoid overwhelming servers
- Use parallel execution with caution to prevent system overload 