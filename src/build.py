name = f"veeru.com"
domain = "veeru.com"
generic_username = "veerup"
twitter_username = f"@{generic_username}"
url = f"https://{domain}"  # for opengraph

import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from shutil import rmtree
import argparse

from jinja2 import Environment, FileSystemLoader, select_autoescape
import mistune, frontmatter


def bs(content):
    return BeautifulSoup(content, "html.parser")


parser = argparse.ArgumentParser(description="Build the website")
parser.add_argument("--output", help="Output directory", default="dist")
parser.add_argument(
    "--no-clean", help="Don't clean the output directory", action="store_true"
)

args = parser.parse_args()

script_path = os.path.dirname(os.path.realpath(__file__))

env = Environment(
    loader=FileSystemLoader(f"{script_path}/templates"),
    autoescape=select_autoescape(["html"]),
)

if not args.no_clean:
    # delete everything inside the output directory
    for root, dirs, files in os.walk(args.output):
        for file in files:
            if file == "index.css":
                continue
            os.remove(os.path.join(root, file))

        for dir in dirs:
            rmtree(os.path.join(root, dir))


def write_output(content, *path):
    # make sure every directory in the path exists
    for i in range(len(path) - 1):
        if not os.path.exists(os.path.join(args.output, *path[: i + 1])):
            os.makedirs(os.path.join(args.output, *path[: i + 1]))

    with open(os.path.join(args.output, *path), "w") as f:
        f.write(content)


def og_tags(data: dict):
    tags = []
    for key, value in data.items():
        tags.append(f'<meta property="og:{key}" content="{value}">')

    return tags


class Services:
    def __init__(self):
        content_root = os.path.join("posts", "services")
        services = os.listdir(content_root)

        self.services = {}
        for service in services:
            metadata_file = os.path.join(content_root, service, "service.md")
            if not os.path.exists(metadata_file):
                raise Exception(f"No service.md file found for {service}")

            fm = frontmatter.load(metadata_file)
            fm["slug"] = service
            self.services[service] = fm

    def slugs(self):
        sorted_keys = sorted(self.services.keys(), key=lambda x: self.services[x]["rank"])
        return sorted_keys

    def render_list(self):
        template = env.get_template(f"posts/services/list.html")
        service_list = [self.services[slug] for slug in self.slugs()]
        return template.render(posts=service_list)

    def service_listings(self, slug):
        listings = set(os.listdir(os.path.join("posts", "services", slug))) - {"service.md"}
        out = []
        for listing in listings:
            fm = frontmatter.load(os.path.join("posts", "services", slug, listing))
            fm["slug"] = f"{slug}/{listing.replace('.md', '')}"

            out.append(fm)

        out = sorted(out, key=lambda x: x["rank"])
        return out

    def render_post(self, slug):
        post = self.services[slug]
        listings = list(self.service_listings(slug))

        template = env.get_template(f"posts/services/page.html")
        rendered = template.render(
            post=post, listings=listings, title=f"{name} | {post['title']}", name=name
        )

        return rendered


twitter_tags_common = {
    "domain": domain,
    "card": "summary_large_image",
    "site": twitter_username,
}


def twitter_tags(data: dict):
    lut = {
        "card": "name",
        "domain": "property",
        "url": "property",
        "title": "name",
        "description": "name",
        "image": "name",
        "site": "name",
    }

    data = {**twitter_tags_common, **data}

    tags = []
    for key, value in data.items():
        tags.append(f'<meta {lut[key]}="twitter:{key}" content="{value}">')

    return tags


# def post_seotags(folder, post):
#     items_common = {
#         "url": urljoin(url, f"/{folder}/{post['slug']}"),
#     }

#     if "title" in post:
#         items_common["title"] = f"{name} | {post['title']}"

#     if "summary" in post:
#         items_common["description"] = post["summary"]

#     if "coverImage" in post:
#         items_common["image"] = urljoin(url, post["coverImage"])

#     items_og = {
#         **items_common,
#         "type": "website",
#     }

#     items_twitter = {
#         **items_common,
#         "card": "summary_large_image",
#         "domain": domain,
#     }

#     return og_tags(items_og) + twitter_tags(items_twitter)


# def render_post(folder, post):
#     template = env.get_template(f"posts/{folder}/page.html")
#     rendered = template.render(post=post, title=f"{name} | {post['title']}", name=name)

#     soup = bs(rendered)
#     og = post_seotags(folder, post)

#     for item in og:
#         soup.head.append(bs(item))

#     return soup.renderContents().decode("utf-8")


# def render_post_list(folder, posts):
#     template = env.get_template(f"posts/{folder}/list.html")
#     return template.render(posts=posts)

type_class = {
    "services": Services
}

post_folders = [f for f in os.listdir("posts") if os.path.isdir(f"posts/{f}")]
lists = {}

for post_folder in post_folders:
    obj = type_class[post_folder]()
    slugs = obj.slugs()

    for slug in slugs:
        # write_output(
        #     render_post(post_folder, post), post_folder, f"{post['slug']}.html"
        # )
        write_output(
            obj.render_post(slug),
            post_folder,
            f"{slug}.html",
        )

    # lists[post_folder] = render_post_list(post_folder, posts)
    lists[post_folder] = obj.render_list()


# seo_common = {
#     "url": url,
#     "title": name,
#     "description": f"{name} service catalog",
#     "image": urljoin(url, "/assets/me.jpg"),
# }

# og = og_tags(
#     {
#         **seo_common,
#         "type": "website",
#     }
# )

# twitter = twitter_tags({**seo_common, "card": "summary"})
# seotags = og + twitter

index = env.get_template("index.html")
rendered = index.render(lists=lists, name=name, title=name)

soup = bs(rendered)
# for item in seotags:
#     soup.head.append(bs(item))

write_output(soup.renderContents().decode("utf-8"), "index.html")
