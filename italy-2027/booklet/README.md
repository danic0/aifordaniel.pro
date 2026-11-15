# Sicily booklet

`make.py` builds `../sicily-booklet.pdf` (one A4 page per day) from `../index.html`.
It runs automatically on GitHub (`.github/workflows/booklet.yml`) whenever `index.html` changes.

Local build:

    cd italy-2027/booklet && npm install && pip install beautifulsoup4 qrcode playwright
    python3 make.py        # set CHROME_PATH to use an installed Chrome

Restaurant, bar and site names in the PDF link to Google Maps. Names are taken from the
restaurant and bar cards in `index.html`; other bold names fall back to a Maps search.
