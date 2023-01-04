=======
# PlotScrapper

Tool used to quickly find plots of lands to support [Protect Earth's](https://www.protect.earth/) reforestation efforts based on the land requirements.


## Setup

1. Install requirements

```bash
pip install -r requirements.txt
```

2. [Download geckodriver](https://github.com/mozilla/geckodriver/releases) for Mozilla Firefox.

3. Place the `geckodriver.exe` into the root of this project.

4. Change the install location for Firefox (if required) in `addland.py`:

```python
options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
```

## Run

The script will run through various searches and, if it finds any matches, it will open them in your browser for final review before forwarding them to Protect Earth discord channel.

```bash
python3 main.py
```
