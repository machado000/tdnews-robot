#!/home/joaom/Projects/tdnews-robot/.venv/bin/python

import asyncio
import os
import pendulum  # noqa
import random
from playwright.async_api import async_playwright
from playwright._impl._errors import TimeoutError
from time import sleep


def main():
    '''
    Main function to execute the job.
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
    Visit a page with a rotated header and take a screenshot
    '''
    # Select a random device from Playwright devices
    device_name = random.choice(list(playwright.devices.keys()))
    device = playwright.devices[device_name]  # Get the device configuration

    browser = await playwright.chromium.launch(
        headless=True,
        proxy={
            'server': 'http://p.webshare.io:80',
            'username': 'holoscompany-rotate',
            'password': 'tgbsphkipr6q'
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

    # Filter links that contain 'https://tododianews.com.br/noticia/'
    filtered_links = await page.locator('a[href*="https://tododianews.com.br/noticia/"]').element_handles()

    for i in range(0, scroll_height, 100):
        await page.evaluate(f'window.scrollTo(0, {i});')
        await page.wait_for_timeout(100)  # Adjust the wait time for slower/faster scroll

    if filtered_links:
        random_link = random.choice(filtered_links)
        href_value = await random_link.get_attribute('href')
        print(f'{proxy_ip} - {device_name} - {href_value.replace('https://tododianews.com.br', '')}')

        try:
            await random_link.click(timeout=30000)  # Click the random link
            await page.wait_for_load_state('load', timeout=30000)  # Wait for the page to fully load
        except TimeoutError:
            print('Element not visible or clickable.')

    else:
        print('No matching links found.')

    # # Save the screenshot
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
    Run multiple page visits concurrently.
    '''
    async with async_playwright() as playwright:
        tasks = []
        for _ in range(simultaneous_runs):
            # headers = random.choice(header_list)
            tasks.append(visit_page(playwright, page_to_visit))

        await asyncio.gather(*tasks)

    return None


async def save_device_list_to_file() -> None:
    async with async_playwright() as playwright:
        all_devices = playwright.devices

        with open('device_list.txt', 'w') as file:
            for device_name in all_devices:
                file.write(f"{device_name}\n")

    return None


def random_coordinates(radius_km=50) -> dict:
    # Brasília coordinates
    latitude_brasilia = -15.8267
    longitude_brasilia = -47.9218

    # Convert km to degrees (1 degree ~ 111 km)
    radius_in_degrees = radius_km / 111

    lat_offset = random.uniform(-radius_in_degrees, radius_in_degrees)
    lon_offset = random.uniform(-radius_in_degrees, radius_in_degrees)

    latitude = latitude_brasilia + lat_offset
    longitude = longitude_brasilia + lon_offset

    return {"longitude": longitude, "latitude": latitude}


if __name__ == '__main__':
    main()
    # asyncio.run(save_device_list_to_file())
