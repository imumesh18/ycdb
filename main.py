import csv
import json
import os

import requests

url = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(3.35.1)%3B%20Browser%3B%20JS%20Helper%20(3.4.4)&x-algolia-application-id=45BWZJ1SGC&x-algolia-api-key=Zjk5ZmFjMzg2NmQxNTA0NGM5OGNiNWY4MzQ0NDUyNTg0MDZjMzdmMWY1NTU2YzZkZGVmYjg1ZGZjMGJlYjhkN3Jlc3RyaWN0SW5kaWNlcz1ZQ0NvbXBhbnlfcHJvZHVjdGlvbiZ0YWdGaWx0ZXJzPSU1QiUyMnljZGNfcHVibGljJTIyJTVEJmFuYWx5dGljc1RhZ3M9JTVCJTIyeWNkYyUyMiU1RA%3D%3D"

headers = {
    "Connection": "keep-alive",
    "accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "content-type": "application/x-www-form-urlencoded",
    "Sec-GPC": "1",
    "Origin": "https://www.ycombinator.com",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://www.ycombinator.com/",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
}

if not os.path.exists("./responses"):
    os.mkdir("./responses")

print("Looking for batches")
request_body = json.dumps(
    {
        "requests": [
            {
                "indexName": "YCCompany_production",
                "params": "query=&hitsPerPage=1&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&analytics=false&facets=%5B%22top_company%22%2C%22isHiring%22%2C%22nonprofit%22%2C%22batch%22%2C%22industries%22%2C%22subindustry%22%2C%22status%22%2C%22regions%22%5D&sortFacetValuesBy=count",
            }
        ]
    }
)

response = requests.post(url, headers=headers, data=request_body)
data = response.json()
batches = list(data["results"][0]["facets"]["batch"].keys())
with open("./responses/yc_batches.json", "w") as f:
    json.dump(batches, f)
print("Batches found")

with open("./responses/yc_batches.json", "r") as f:
    batches = json.load(f)

for batch in batches:
    print(f"Requesting {batch} data")
    request_body = json.dumps(
        {
            "requests": [
                {
                    "indexName": "YCCompany_production",
                    "params": f"hitsPerPage=1000&query=&page=0&facets=%5B%22top_company%22%2C%22isHiring%22%2C%22nonprofit%22%2C%22batch%22%2C%22industries%22%2C%22subindustry%22%2C%22status%22%2C%22regions%22%5D&tagFilters=&facetFilters=%5B%5B%22batch%3A{batch}%22%5D%5D",
                }
            ]
        }
    )

    response = requests.post(url, headers=headers, data=request_body)
    with open(f"./responses/{batch}.json", "w") as f:
        f.write(response.text)
    print(f"{batch} data found")

print("All data downloaded")

print("Initiating local processing")

if not os.path.exists("./data"):
    os.makedirs("./data")

path = "./responses"
with open("./data/combined_companies_data.json", "w") as outfile:
    outfile.write("[")
    for filename in os.listdir(path):
        if filename == "yc_batches.json":
            continue

        print(f"Processing {filename}")
        with open(f"{path}/{filename}", "r") as infile:
            file_data = json.load(infile)
            useful_data = file_data["results"][0]["hits"]
            if filename == os.listdir(path)[0]:
                outfile.write(json.dumps(useful_data)[1:-1])
            else:
                outfile.write("," + json.dumps(useful_data)[1:-1])
        print(f"Processed {filename}")
    outfile.write("]")

print("All data combined into single JSON")

print("Stripping company data to essentials")

with open("./data/combined_companies_data.json", "r") as f:
    data = json.load(f)

stripped_data = [
    {k: v for k, v in item.items() if k != "_highlightResult"} for item in data
]

with open("./data/yc_essential_data.json", "w") as f:
    json.dump(stripped_data, f)

print("Stripping JSON data complete")

print("Converting essential data JSON to CSV")

with open("./data/yc_essential_data.json", "r") as json_file:
    data = json.load(json_file)

sorted_data = sorted(data, key=lambda x: x["id"])

with open("./data/yc_essential_data.csv", "w", newline="") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(sorted_data[0].keys())
    for row in sorted_data:
        writer.writerow(row.values())

print("JSON to CSV conversion complete")
