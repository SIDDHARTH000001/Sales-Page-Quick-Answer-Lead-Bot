# Sales-Page-Quick-Answer-Lead-Bot

## Team - 26
## Project Name - Sales Page Quick-Answer & Lead Bot

🎥 [Watch Demo](https://youtu.be/xhdFA_UGAE4)

## 📌 Overview
An AI-powered lead management and qualification app.  
It captures prospect information such as **name, email, company, and company size** and enriches it with behavioral signals:  

- **Pages visited**  
- **Time spent on each page**  
- **Number of questions asked**  

Using these signals, the app automatically decides whether the prospect is a **potential customer** (hot/warm lead) or not.

All captured leads are stored in an Excel file (`leads.xlsx`) with relevant details and a timestamp.

---

## ⚙️ Features
- Extracts **lead details** from free-form user input.  
- Tracks **behavioral signals** (page visits, time, questions asked).  
- Automatically computes **qualification score** and **lead quality**.  
- Saves structured data into an Excel file.  
- Built with **Streamlit** for an interactive UI.  

---

## 🚀 Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SIDDHARTH000001/Sales-Page-Quick-Answer-Lead-Bot.git
   cd Sales-Page-Quick-Answer-Lead-Bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Running the App

Once the setup is complete, run:

```bash
streamlit run app.py --server.fileWatcherType=none
```

You’ll see an output like:

```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.0.103:8501
```

Open the **Local URL** in your browser to start using the app.

---

## 📂 Lead Storage Format

All captured leads are appended to **`leads.xlsx`** with the following structure:

| capture_timestamp     | full_name | work_email                                   | company | qualification_score | lead_quality | pages_visited  | questions_asked | time_to_capture |
| --------------------- | --------- | -------------------------------------------- | ------- | ------------------- | ------------ | -------------- | --------------- | --------------- |
| 2025-09-14T11:13:02.09 | John Doe | [johndoe@gmail.com](mailto:johndoe@gmail.com) | Acme Co | 82                  | hot          | /home, /pricing | 3               | 120             |

---

## 🛠️ Tech Stack

* **Python 3.11+**
* **Streamlit**
* **Pandas / OpenPyXL**
* **LangChain & LangGraph**
* **Sentence-Transformers**
* **FAISS** (for embeddings & search)

---