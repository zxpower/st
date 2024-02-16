# AS Sadales Tīkls Electricity Consumption Scraper

Script allows you to scrape your smart electricity meter consumption data from [AS Sadales tīkls klientu portāls](https://mans.e-st.lv) website for selected period (`day`, `month` or `year`) and output it to file in JSON format or output to console.

## Example usage

Example code is included in `main.py` file. To start using script first prepare environment and install necessary packages:

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Then you can run following command by replacing `username` with your Mans e-ST portal's username, `password` with your password, `objectid` and `meter` params could be obtained from Mans e-ST [Objektu informācija](https://mans.e-st.lv/lv/private/objektu-parskats/) page by inspecting your property details and looking for "Objekta EIC kods" and "Skaitītāja numurs".

```bash
python3 main.py \
    --username 'username' \
    --password 'password' \
    --objectid 'objectid' \
    --meter meter \
    --period day \
    --year 2024 \
    --month 02 \
    --day 14 \
    --neto True \
    --outfile data.json
```
