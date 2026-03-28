# ToneVault

> A digital inventory and signal chain manager for guitarists.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0+-092E20.svg)

ToneValt is an application to help musicians organize their gear collection and remember the exact settings (signal chains) used for specific genres/songs. 

## Features
* **Gear Vault:** Manage your guitars, amps, and pedals (from a global catalog or add custom items).
* **Signal Chains:** Build song-specific setups with exact pedal order and knob settings.
* **Community:** Share your legendary tones and discover setups from other users.

## Architecture
This project goes beyond basic CRUD by implementing enterprise-level design patterns to keep the business logic clean, testable, and scalable.

 **[Full Architecture & Design Patterns documentation](ARCHITECTURE.md)**

##  Quick Start

Get the app running locally with a fully populated database:

1. **Setup environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
2. **Setup Database & Seed Data**
```bash
python manage.py migrate
python manage.py seed_gear   # Loads global gear catalog
python manage.py seed_users  # Loads user community and setups
```
3. **Run**
```bash
python manage.py runserver
```
4. **Test account**: Login as `jimi_hendrix` with password `purple_haze`

## Preview

1. **Profile page**
<img width="2503" height="1332" alt="image" src="https://github.com/user-attachments/assets/0682762f-e6fa-416d-b326-77b1d095f373" />


2. **Setup configuration**
<img width="2503" height="1332" alt="image" src="https://github.com/user-attachments/assets/7a41b4c7-6796-40b1-b4fd-e94b4fdb0c6d" />


3. **User's collection**
<img width="2503" height="1332" alt="image" src="https://github.com/user-attachments/assets/ccfcb7dc-11c0-45b8-85ff-d884f59bac62" />

