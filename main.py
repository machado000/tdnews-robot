#!/home/joaom/Projects/pagevisit-robot/.venv/bin/python

import asyncio
import os
import pendulum  # noqa
import random
from playwright.async_api import async_playwright
from playwright._impl._errors import TimeoutError
from time import sleep


def main():
    '''
    Main function to run a asynchronous job, visiting a specified page repeatedly
    using multiple browser instances to mimic user behavior.
    '''
    page_to_visit = 'https://tododianews.com.br'
    cpu_cores = os.cpu_count() or 1  # Get the number of CPU cores
    simultaneous_runs = min(cpu_cores, 10)  # Limit simultaneous runs

    while True:
        # Execute the async function
        try:
            # Use the executor to run the job function
            asyncio.run(job(page_to_visit, simultaneous_runs))

        except Exception as e:
            print(f'Error occurred: {e}')
            print('Restarting the job...')
            sleep(60)  # Optional: delay before retrying


async def visit_page(playwright, page_to_visit) -> None:
    '''
    Visit a page with a rotated device/header.

    Args:
        playwright: The playwright instance to launch the browser.
        page_to_visit: The URL of the page to visit.
    '''
    # Select a random device from Playwright devices
    device_name = random.choice(list(playwright.devices.keys()))
    device = playwright.devices[device_name]  # Get the device configuration

    # Get proxy settings from environment variables
    proxy_server = 'http://p.webshare.io:80'
    proxy_username = os.getenv('PROXY_USERNAME')  # Proxy username from .env
    proxy_password = os.getenv('PROXY_PASSWORD')  # Proxy password from .env

    browser = await playwright.chromium.launch(
        headless=True,
        proxy={
            'server': proxy_server,
            'username': proxy_username,
            'password': proxy_password
        },
    )

    coordinates = random_coordinates()

    context = await browser.new_context(
        **device,
        locale='pt-BR',
        timezone_id='America/Sao_Paulo',
        geolocation=coordinates,
        permissions=['geolocation']
    )

    page = await context.new_page()

    await page.goto('https://ipv4.webshare.io/')
    proxy_ip = await page.evaluate('document.body.innerText')

    await page.goto(page_to_visit)

    # Scroll down to the bottom of the page
    scroll_height = await page.evaluate('document.body.scrollHeight')

    for i in range(0, scroll_height, 100):
        await page.evaluate(f'window.scrollTo(0, {i});')
        await page.wait_for_timeout(100)  # Adjust the wait time for slower/faster scroll

    # Filter links that contain 'https://tododianews.com.br/noticia/', adjust as needed
    filtered_links = await page.locator('a[href*="https://tododianews.com.br/noticia/"]').element_handles()

    if filtered_links:
        random_link = random.choice(filtered_links)
        href_value = await random_link.get_attribute('href')
        print(f'{proxy_ip} - {device_name} - {href_value.replace("https://tododianews.com.br", "")}')

        try:
            await random_link.click(timeout=30000)  # Click the random link on filtered list
            await page.wait_for_load_state('load', timeout=30000)  # Wait for the page to fully load
        except TimeoutError:
            print('Element not visible or clickable.')
    else:
        print('No matching links found.')

    # Save the screenshot (if needed)
    # os.makedirs('screenshots', exist_ok=True)
    # timestamp = pendulum.now().format('YYYYMMDD-HHmmss-SSSS')
    # filepath = os.path.join('screenshots', f'{timestamp}.png')
    # await page.screenshot(path=filepath)
    # print(f'Saved screenshot as {filepath}')

    await context.close()
    await browser.close()

    return None


async def job(page_to_visit: str, simultaneous_runs: int) -> None:
    '''
    Run multiple visit_page() methods concurrently.

    Args:
        page_to_visit: The URL of the page to visit.
        simultaneous_runs: The number of concurrent page visits.
    '''
    async with async_playwright() as playwright:
        tasks = [visit_page(playwright, page_to_visit) for _ in range(simultaneous_runs)]
        await asyncio.gather(*tasks)

    return None


async def save_device_list_to_file() -> None:
    '''
    Save the list of available devices to a text file for reference.
    '''
    async with async_playwright() as playwright:
        all_devices = playwright.devices

        with open('device_list.txt', 'w') as file:
            for device_name in all_devices:
                file.write(f"{device_name}\n")

    return None


def random_coordinates(latitude_origin: float = None, longitude_origin: float = None, radius_km=50) -> dict:
    '''
    Generate random geographic coordinates within a specified radius.

    Args:
        latitude_origin (float): The origin latitude; defaults to Brasília's latitude if not provided.
        longitude_origin (float): The origin longitude; defaults to Brasília's longitude if not provided.
        radius_km (int): The radius in kilometers to generate random coordinates.

    Returns:
        dict: A dictionary with random longitude and latitude.
    '''
    # Default coordinates for Brasília, Brazil, if not provided
    latitude_origin = latitude_origin or -15.8267
    longitude_origin = longitude_origin or -47.9218

    # Convert kilometers to degrees (approximately 1 degree ~ 111 km)
    radius_in_degrees = radius_km / 111

    # Generate random offsets within the specified radius
    lat_offset = random.uniform(-radius_in_degrees, radius_in_degrees)
    lon_offset = random.uniform(-radius_in_degrees, radius_in_degrees)

    # Calculate the new random latitude and longitude
    latitude = latitude_origin + lat_offset
    longitude = longitude_origin + lon_offset

    return {"longitude": longitude, "latitude": latitude}


if __name__ == '__main__':
    main()
    # asyncio.run(save_device_list_to_file())
