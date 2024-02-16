## Usenet Google Groups Scraper
This project is a Python script that scrapes Google Groups data. It uses Selenium WebDriver with Firefox to navigate the Google Groups website and extract links to posts.

## Project Structure
`scraping_googlegroups.py`: This is the main script that performs the scraping.

## How to Run
Ensure you have Python and Selenium WebDriver installed on your machine, along with the Firefox browser.
Put a list of Google Groups URLs in a file named group_list.txt, with one URL per line.
Run the script with the command `python scraping_googlegroups.py group_list.txt`.

## Output
The script will generate a CSV file named lista_link_it.aiuto.csv with the following structure:

`link`: This is a link to a post in a Google Group.
`anno`: This is the year the post was made.
`mese`: This is the month the post was made.
`pagina`: This is the page number where the post was found.

## Contributing
Contributions are welcome. Please open an issue to discuss your idea or submit a Pull Request.

## License
This project is licensed under the MIT License. See the LICENSE file for details. 