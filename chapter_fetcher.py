#!/usr/bin/env python

import argparse
import os.path
import re
import requests
import time


def build_filename(idx):
    res = f"p-{idx:03d}.html"
    return res


def build_full_out_file_name(dir, i):
    file_name = build_filename(i)
    return f'{dir}/{file_name}'


def find_filler_id(text):
    found = re.search(br"<style>\s*([^<>]*)\s*{[^<>]*</style>", text, re.S | re.I | re.M)
    if found is None:
        return
    else:
        return found.group(1)


def remove_filler(text):
    filler = find_filler_id(text)
    regex = b'<' + filler + b'>' + b'[^<>]*' + b'</' + filler + b'>'
    res = re.sub(regex, b'', text, re.S | re.I | re.M)
    return res


def replace_ad_links(data):
    res1 = re.sub(br'<link[^<>]+href="https://www.googletagmanager.com"[^<>]*/>', b'', data, re.I | re.S | re.M)
    res2 = re.sub(br'<link[^<>]+href="https://adservice.google.com"[^<>]*/>', b'', res1, re.I | re.S | re.M)
    res3 = re.sub(br'<div[^<>]*>[^<>]*<ins[^<>]+class="ads[^<>]*>[^<>]*</ins[^<>]*>[^<>]*</div[^<>]*>', b'', res2,
                  re.I | re.S | re.M)
    return res3


def replace_prev_page(idx, data):
    prev_idx = idx - 1
    filename = build_filename(prev_idx)
    replacement = f"\\1{filename}\\2".encode('utf-8')
    res = re.sub(rb'(<a\s+title\s*=\s*["\']Previous Chapter["\'][^<>]*\bhref=["\'])[^<>"\']+(["\'][^<>]*>)',
                 replacement, data, re.S | re.I | re.M)
    return res


def replace_next_page(idx, data):
    next_idx = idx + 1
    filename = build_filename(next_idx)
    replacement = f'\\1{filename}\\2'.encode('utf-8')
    res = re.sub(rb'(<a\s+title\s*=\s*["\']Next Chapter["\'][^<>]*\bhref=["\'])[^<>"\']+(["\'][^<>]*>)',
                 replacement, data, re.S | re.I | re.M)
    return res


def replace_ad_banner(data):
    res = re.sub(
        rb'<div[^<>]*class="banner[^<>]*>[^<>]*<div[^<>]*>[^<>]*<script>[^<>]*</script>[^<>]*</div>[^<>]*</div>', b'',
        data, re.S | re.I | re.M)
    return res


def replace_script(data):
    res = re.sub(rb"<script.*?<\/script>", b"", data, 0, re.S | re.I | re.M)
    return res


def replace_svg(data):
    res = re.sub(rb"<svg.*?<\/svg>", b"", data, 0, re.S | re.I | re.M)
    return res


def remove_spacer1(data):
    res = re.sub(rb"<div class=\"mantine-1ccs8mh\">\s*</div>", b"", data, 0, re.S | re.I | re.M)
    return res


def remove_spacer2(data):
    res = re.sub(rb"<div[^<>]*>[^<>]*Read Latest Chapters at[^<>]*</div>", b"", data, 0, re.S | re.I | re.M)
    return res


def make_out_dir(indir):
    out_dir = f"{indir}-out"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    return out_dir


def sub_one_data(data, idx):
    d1 = data
    d2 = remove_filler(d1)
    d3 = replace_ad_banner(d2)
    d4 = replace_prev_page(idx, d3)
    d5 = replace_next_page(idx, d4)
    d6 = replace_script(d5)
    d7 = replace_svg(d6)
    d8 = remove_spacer1(d7)
    d9 = remove_spacer2(d8)
    d10 = replace_ad_links(d9)
    return d10


def sub_one(data, idx):
    binary_data = data.encode('utf-8')
    res = sub_one_data(binary_data, idx)
    return res


def fetch_one_chapter(args, url, i):
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux i686; rv:128.0) Gecko/20100101 Firefox/128.0'
    }
    r = requests.get(
        url,
        headers=headers
    )
    if r.status_code in range(200, 400):
        return r.text
    else:
        raise ("Http error", r)


def extract_next_url(text):
    second_half = re.search(r'\bchapter-title\b(.*)', text, re.S | re.I | re.M)
    if second_half:
        g1 = second_half.group(1)
        middle_part = re.search(r'(.*)\bchapter-container\b', g1, re.S | re.I | re.M)
        if middle_part:
            g2 = middle_part.group(1)
            a_tag = re.search(r'<(a[^<>]*title=[^<>]*"Next\s*Chapter"[^<>]*)>', g2, re.S | re.I | re.M)
            if a_tag:
                g3 = a_tag.group(1)
                href_part=re.search(r'\bhref\s*=\s*["\'](\S*)["\']', g3, re.S | re.I | re.M)
                if href_part:
                    next_url = href_part.group(1)
    return next_url


def create_out_dir(dir):
    os.makedirs(dir, exist_ok=True)


def write_one_chapter(args, i, data):
    out_file = build_full_out_file_name(args.out_dir, i)
    with open(out_file, "wb") as fd:
        fd.write(data)


def process_one_chapter(args, url, i):
    data = fetch_one_chapter(args, url, i)
    next_url = extract_next_url(data)
    cleaned_data = sub_one(data, i)
    write_one_chapter(args, i, cleaned_data)
    return next_url


def get_initial_args():
    parser = argparse.ArgumentParser(description='Process some dirs.')
    parser.add_argument('--host', help='host')
    parser.add_argument('--title', help='title as in url')
    parser.add_argument('--first', type=int, help='first page')
    parser.add_argument('--last', type=int, help='last page')
    parser.add_argument('--out_dir', help='output directory', default='output')
    parser.add_argument('--delay', type=float, help='delay after fetching every page')
    args = parser.parse_args()
    return args


def build_initial_url(args):
    return (
            "https://" +
            args.host +
            "/book/" +
            args.title +
            "/chapter-" +
            str(args.first)
    )


def get_args():
    initial_args = get_initial_args()
    initial_url = build_initial_url(initial_args)
    parser = argparse.ArgumentParser(description='Process some dirs.')
    parser.add_argument('--initial_url', help='initial url', default=initial_url)
    parser.add_argument('--host', help='host', default=initial_args.host)
    parser.add_argument('--title', help='title as in url', default=initial_args.title)
    parser.add_argument('--first', type=int, help='first page', default=initial_args.first)
    parser.add_argument('--last', type=int, help='last page', default=initial_args.last)
    parser.add_argument('--out_dir', help='output directory', default=initial_args.out_dir)
    parser.add_argument('--delay', type=float, help='delay after fetching every page',
                        default=initial_args.delay)
    args = parser.parse_args()
    return args


def delay(args):
    time.sleep(args.delay)


def run():
    args = get_args()
    create_out_dir(args.out_dir)
    next_url = args.initial_url
    for i in range(args.first, args.last + 1):
        next_url = process_one_chapter(args, next_url, i)
        delay(args)


run()
