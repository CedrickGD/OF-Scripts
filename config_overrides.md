# OF-Scraper Config Overrides

Manual settings to apply in ofscraper's `config.json` when needed.

---

## Directory Format — Media Type Only

Sorts files into folders by media type only (Images, Videos, Audio), without splitting by response type (Posts, Messages, Archived, etc.).

**Setting:** `file_options.dir_format`

```
{model_username}/{mediatype}/
```

**Result:**
```
username/Images/
username/Videos/
username/Audio/
```

**Default (ofscraper):**
```
{model_username}/{responsetype}/{mediatype}/
```
