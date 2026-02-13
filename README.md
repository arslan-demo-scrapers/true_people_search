# Web Scraper Setup & Usage Guide

## 1. Prerequisites

* Python 3.6+
* PyCharm Community Edition (recommended)
* MySQL Server
* MySQL Workbench

---

## 2. Environment Setup

### Install and Open Project

1. Install **PyCharm Community Edition**
2. Open the project root directory

---

### Create Virtual Environment

In PyCharm:

* Go to **File → Settings → Project → Python Interpreter**
* Create a new virtual environment

---

### Upgrade pip

```bash
pip install --upgrade pip
```

---

### Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

If needed, install manually:

```bash
pip install Scrapy==2.13.4
pip install scrapeops-scrapy
```

---

## 3. Environment Variables (.env Setup)

Create a `.env` file in the project root directory (same level as `scrapy.cfg`) and add:

```env
SCRAPEOPS_API_KEY=your_api_key_here
```

> Replace `your_api_key_here` with your personal ScrapeOps proxy API key.

**Important:**

* The `.env` file must be placed in the project root directory.

---

## 4. MySQL Setup

### Install MySQL

* Download and install:

    * **MySQL Server**
    * **MySQL Workbench**

### Create Database & Tables

1. Open MySQL Workbench
2. Create a new database
3. Create required tables according to the project schema

---

## 5. Running the Spider

1. Open the terminal/command prompt and navigate to the project directory:

   ```sh
   cd "true_people_search/true_people_search/spiders"
   ```

2. Run the script using syntax:

   ```sh
   scrapy crawl true_people_search_spider
   ```

   **OR**

   Open `true_people_search_spider.py` in PyCharm, right-click on it, and select the `Run` option.

**Note:**

Make sure you are in the project spiders directory:

```
/true_people_search/true_people_search/spiders/
```

---

## 6. Output

After execution, the scraper will:

* Perform search queries
* Extract structured data
* Save results to the `output/` folder

The output file format is:

* JSON (`.json`)

---

### Notes

* Ensure your virtual environment is activated before running the spider.
* Ensure the `.env` file contains your `SCRAPEOPS_API_KEY`.
* Confirm MySQL is running if database storage is enabled.
* If you need assistance, feel free to reach out.

Best regards,
**Arslan**
