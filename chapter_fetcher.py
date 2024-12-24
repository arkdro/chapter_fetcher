#!/usr/bin/env python

import argparse
import os.path
import re

def build_filename(idx):
	res = f"p-{idx:03d}.html"
	return res

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
	res1 = re.sub(br'<link[^<>]+href="https://www.googletagmanager.com"[^<>]*/>', b'', data, re.I|re.S|re.M)
	res2 = re.sub(br'<link[^<>]+href="https://adservice.google.com"[^<>]*/>', b'', res1, re.I|re.S|re.M)
	res3 = re.sub(br'<div[^<>]*>[^<>]*<ins[^<>]+class="ads[^<>]*>[^<>]*</ins[^<>]*>[^<>]*</div[^<>]*>', b'', res2, re.I|re.S|re.M)
	return res3

def replace_prev_page(idx, data):
	prev_idx = idx - 1
	filename = build_filename(prev_idx)
	prev_replace = f"\\1\"{filename}\"\\2".encode('ascii')
	res = re.sub(br"(<a href=)[^<> ]*([^<>]*>[^<>]*<div[^<>]*>[^<>]*<button[^<>]*>[^<>]*<div[^<>]*>[^<>]*<span[^<>]*>[^<>]*<div[^<>]*>[^<>]*(?:<[^<>]*>)?[^<>]*Previous Chapter)", prev_replace, data, re.I|re.S|re.M)
	return res

def replace_next_page(idx, data):
	next_idx = idx + 1
	filename = build_filename(next_idx)
	next_replace = f"\\1\"{filename}\"\\2".encode('ascii')
	res = re.sub(br"(<a href=)[^<> ]*([^<>]*>[^<>]*<div[^<>]*>[^<>]*<button[^<>]*>[^<>]*<div[^<>]*>[^<>]*<span[^<>]*>[^<>]*<div[^<>]*>[^<>]*(?:<[^<>]*>)?[^<>]*Next Chapter)", next_replace, data, re.I|re.S|re.M)
	return res

def replace_ad_banner(data):
	res = re.sub(rb'<div[^<>]*class="banner[^<>]*>[^<>]*<div[^<>]*>[^<>]*<script>[^<>]*</script>[^<>]*</div>[^<>]*</div>', b'', data, re.S | re.I | re.M) 
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

def sub_one(idx, indir):
	in_filename = build_filename(idx)
	f1 = f"{indir}/{in_filename}"
	if not os.path.isfile(f1):
		return
	out_dir = make_out_dir(indir)
	f2 = f"{out_dir}/{in_filename}"
	d1 = b""
	with open(f1,"rb") as fd:
		d1 = fd.read()

	d2 = remove_filler(d1)
	d3 = replace_ad_banner(d2)
	d4 = replace_prev_page(idx, d3)
	d5 = replace_next_page(idx, d4)
	d6 = replace_script(d5)
	d7 = replace_svg(d6)
	d8 = remove_spacer1(d7)
	d9 = remove_spacer2(d8)
	d10 = replace_ad_links(d9)

	with open(f2, "wb") as fd:
		fd.write(d10)

def get_args():
	parser = argparse.ArgumentParser(description='Process some dirs.')
	parser.add_argument('--indir', help='input dir')
	parser.add_argument('--first', type=int, help='first page')
	parser.add_argument('--last', type=int, help='last page')
	args = parser.parse_args()
	return args

def run():
	args = get_args()
	for i in range(args.first, args.last):
		sub_one(i, args.indir)

run()
