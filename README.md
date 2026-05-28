# SET Kerala Quiz App 📚

A fast, fully offline-capable Progressive Web App (PWA) designed to help students prepare for the **Kerala State Eligibility Test (SET)** by practicing previous years' question papers.

## 🚀 Features

- **Years Covered:** Previous question papers from **2015 to 2025** (June, July, December, etc.).
- **Learning-First Design:** Immediate feedback upon answering, with options disabling after your first try to prevent mindless clicking and enforce learning.
- **Offline Capable:** Fully installable as a PWA on your mobile or desktop device. Practice questions anywhere, even without internet access!
- **Data Integrity:** Accurate, clean parsing of 120 questions per paper with exact answer keys.

## 🛠 Tech Stack

- **Frontend:** Vanilla HTML5, CSS3, JavaScript (No frameworks used, making it incredibly lightweight and fast)
- **Data Extraction:** Python script (`extract_layout.py`) to parse massive PDF archives using layout-aware text extraction.
- **Hosting:** GitHub Pages

## 📦 How to Use (Developers)

The raw data from the SET exams is compiled using the `extract_layout.py` python script. 
If you want to add new question papers in the future:
1. Extract the PDF layout text: `pdftotext -layout <pdf-file> extracted_text_layout.txt`
2. Run the parser: `python3 extract_layout.py`
3. The script will automatically update `data.js` with the clean JSON.
4. Don't forget to bump the `CACHE_NAME` version in `sw.js` if you push new data!

## 📱 Installation

Visit the [Live Website](https://sudoanirudh.github.io/set-quiz-app/) on your phone or PC and select "Add to Home Screen" or "Install App" to use it as a native application!
