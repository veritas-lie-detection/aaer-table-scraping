# aaer-table-scraping
### Collecting URLs from SEC's AAERs

The SEC conducts audits companies and releases documents (AAERs) detailing infractions found in tabled format [here](https://www.sec.gov/divisions/enforce/friactions.htm). The infractions are organized by year, which can be navigated by using the links above the table. The table consists of three columns, the "Release No." of the AAER which contains a hyperlink to the document, the "Date" the AAER was published, and the "Respondents" associated with the AAER. There may be repeated respondents depending on the offence, and there may be multiple respondents that correspond to the same offence.

This script extracts the hyperlinks from tables over all years and adds them to an AuroraMySQL table.
The table has the following attributes:

| Column | Type | Description |
| :--- | :--- | :--- |
| url | string | (primary key) The URL of the AAER. |
| publish_date | string | The date the AAER was released. |
| respondents | string | The respondents for the AAER. |
| scraped | bool | Whether the document has been successfully processed by **aaer-pdf-extractor**. |
