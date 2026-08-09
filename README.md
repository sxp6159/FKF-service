# Mohu Budapest hulladéknaptár

Mohu Budapest hulladéknaptár is python script that connects to https://mohubudapest.hu/hulladeknaptar and opens calendar based on parameters, gets details for selective trash and sends email reminder 2 days and 1 day before.

## Installation

Configure .env file and run docker command

```bash
docker compose up -d --build
```
For subsequential runs run docker command
```bash
docker compose down && docker compose up -d --build
```

## Usage

Parameters are configures in fkf.py file as following
```python
LOCATIONS = [
    {
        "district": "1037",
        "publicPlace": "Királylaki---út",
        "houseNumber": "11",
        "recipients": ["srecko_podvinski@yahoo.com", "sapij17@gmail.com"],
    },
    {
        "district": "1037",
        "publicPlace": "Solymárvölgyi---út",
        "houseNumber": "13",
        "recipients": ["srecko_podvinski@yahoo.com"],
    },
]
```
