# InfoSec Final Project (AUCA)

**Student**: Burkhoniddin Khaitkulov (kb12362)  
**Course**: Information Security (AUCA)

This repository contains **educational course projects** created for learning and demonstration purposes.  
I confirm the work here is used for **academic / non-commercial** use, and any external resources (frameworks, public web pages) are used only as references for study and demos.

---

## Projects in this repository

### 1) RealTimeChat — real-time chat + REST bridge

A lightweight real-time chat built with **Flask + Flask-SocketIO** and **SQLite**:

- Real-time messaging (Socket.IO)
- Chat history stored in SQLite
- REST API endpoint that injects messages into the real-time stream (good for Postman demo)
- Basic security improvements (XSS-safe rendering, input validation, parameterized SQL)

**Detailed README**: `RealTimeChat/README.md`

---

### 2) AutomatedWebScraperElasticsearch — automated web scraper + search

A small scraper that parses public movie list pages (Wikipedia) and saves structured rows so you can **search and browse** them:

- Scrape movie list data (title + table fields when available)
- Store records for fast lookup (CLI + minimal web UI on Flask + HTML/CSS)

**Detailed README**: `AutomatedWebScraperElasticsearch/README.md`

---

## Demo videos (YouTube)

- **RealTimeChat demo**: `https://www.youtube.com/watch?v=slPZRRE8mcc`
- **Web scraper demo**: `https://www.youtube.com/watch?v=Ah6_ppRCRjo`
- **Peer review**: `<PASTE_YOUTUBE_LINKS_HERE>`