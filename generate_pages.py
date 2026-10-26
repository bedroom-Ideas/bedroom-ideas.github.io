import os
import sys
import json
import urllib.request
import xml.etree.ElementTree as ET
import shutil

sitemap_url = sys.argv[1] if len(sys.argv) > 1 else "https://stylesdays.com/sitemap_index.xml"
print(f"Fetching sitemap from: {sitemap_url}")

def fetch_url(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_sitemap(url, found_urls=None):
    if found_urls is None:
        found_urls = set()
    
    xml_data = fetch_url(url)
    if not xml_data:
        return found_urls

    try:
        root = ET.fromstring(xml_data)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        sitemaps = root.findall('ns:sitemap', namespace)
        if sitemaps:
            for sm in sitemaps:
                loc = sm.find('ns:loc', namespace)
                if loc is not None and loc.text:
                    print(f"Found sub-sitemap: {loc.text}")
                    parse_sitemap(loc.text, found_urls)
        else:
            urls = root.findall('ns:url', namespace)
            for u in urls:
                loc = u.find('ns:loc', namespace)
                if loc is not None and loc.text:
                    found_urls.add(loc.text.strip())
    except Exception as e:
        print(f"Error parsing XML for {url}: {e}")

    return found_urls

all_urls = parse_sitemap(sitemap_url)
print(f"Total unique URLs found: {len(all_urls)}")

# Fetch WordPress REST API posts to map slugs to real featured images and titles
wp_posts_map = {}
page = 1
while True:
    api_url = f"https://stylesdays.com/wp-json/wp/v2/posts?per_page=100&page={page}&_embed=1"
    print(f"Fetching WordPress REST API batch {page}...")
    data = fetch_url(api_url)
    if not data:
        break
    try:
        posts = json.loads(data.decode('utf-8'))
        if not posts:
            break
        for p in posts:
            slug = p.get('slug')
            title = p.get('title', {}).get('rendered', '')
            # Extract featured image from _embedded if present
            img_url = ""
            try:
                img_url = p.get('_embedded', {}).get('wp:featuredmedia', [{}])[0].get('source_url', '')
            except Exception:
                pass
            
            if slug:
                wp_posts_map[slug] = {
                    "title": title,
                    "image": img_url
                }
        page += 1
    except Exception as e:
        print(f"Error parsing WP API batch {page}: {e}")
        break

print(f"Loaded {len(wp_posts_map)} posts with metadata from WordPress REST API.")

# Exact StylesDays Standalone Editorial Page (Distraction-free: No nav/footer)
EDITORIAL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | stylesdays Editorial Hub</title>
  <meta name="description" content="{description}">
  
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{image}">
  <meta property="og:site_name" content="stylesdays Editorial Hub">
  
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <style>
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: #FAF8F5;
      color: #1C1917;
      -webkit-font-smoothing: antialiased;
    }}
    .font-serif-editorial {{
      font-family: 'Playfair Display', Georgia, serif;
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col selection:bg-[#E60023] selection:text-white">

  <!-- DISCLOSURE BANNER -->
  <div class="w-full bg-[#F1EDE6] border-b border-stone-200/80 text-stone-700 text-xs py-2 px-4">
    <div class="max-w-4xl mx-auto flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center space-x-2">
        <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-stone-900 text-stone-100">
          stylesdays Official Hub
        </span>
        <span class="text-stone-600">
          Curated editorial preview & DIY styling checklist for <strong>stylesdays.com</strong>.
        </span>
      </div>
      <div class="flex items-center space-x-3 text-[11px] font-medium text-stone-500">
        <span>Verified Direct Link</span>
      </div>
    </div>
  </div>

  <!-- MAIN DISTRACTION-FREE CONTENT HUB -->
  <main class="max-w-4xl w-full mx-auto px-4 py-10 flex-grow">
    
    <article class="bg-white rounded-3xl shadow-[0_12px_32px_-8px_rgba(28,25,23,0.06)] border border-stone-200/80 overflow-hidden">
      
      <!-- Hero Image Wrapper -->
      <div class="relative w-full aspect-[16/10] bg-stone-100 overflow-hidden">
        <img 
          src="{image}" 
          alt="{title}" 
          class="relative z-10 w-full h-full object-cover transition-opacity duration-500"
        />

        <!-- Category Badge -->
        <div class="absolute top-4 left-4 z-20 flex items-center gap-2">
          <span class="bg-white/95 backdrop-blur-md text-stone-900 text-xs font-bold uppercase tracking-wider px-3.5 py-1.5 rounded-full shadow-sm border border-stone-200">
            {category}
          </span>
        </div>

        <!-- Transparent Destination Hostname Badge -->
        <div class="absolute bottom-4 right-4 z-20">
          <div class="flex items-center space-x-1.5 bg-stone-900/90 backdrop-blur-md text-white text-xs font-medium px-3.5 py-1.5 rounded-full shadow-md border border-white/15">
            <span class="text-stone-300">Published on:</span>
            <strong class="font-semibold text-white">stylesdays.com</strong>
          </div>
        </div>
      </div>

      <!-- Article Body Content -->
      <div class="p-6 sm:p-10">
        
        <!-- Article Meta Header -->
        <div class="flex flex-wrap items-center justify-between gap-3 text-xs text-stone-500 font-medium mb-4">
          <div class="flex flex-wrap items-center gap-2.5">
            <span class="flex items-center gap-1.5 text-stone-800 font-semibold">
              <svg class="w-4 h-4 text-[#15803D]" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
              </svg>
              <span>stylesdays Editorial Team</span>
            </span>
            <span>•</span>
            <span>6 min full read</span>
            <span>•</span>
            <span>2026 Home & DIY Edition</span>
          </div>
        </div>

        <!-- Editorial Headline -->
        <h1 class="font-serif-editorial text-2xl sm:text-4xl font-bold text-stone-900 leading-tight mb-5">
          {title}
        </h1>

        <!-- Executive Summary Paragraph -->
        <div class="prose prose-stone max-w-none mb-8">
          <p class="text-stone-700 text-base sm:text-lg leading-relaxed font-normal">
            {description}
          </p>
        </div>

        <!-- PRIMARY USER-INITIATED ANCHOR CTA (Above-the-fold accessible & explicit) -->
        <div class="bg-[#FAF8F5] p-5 sm:p-6 rounded-2xl border border-stone-200/90 mb-8">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span class="text-[11px] font-bold uppercase tracking-wider text-stone-400 block mb-1">Full Illustrated Article & Room Photos</span>
              <div class="text-sm font-semibold text-stone-900 flex items-center gap-1.5 flex-wrap">
                <span>Explore all room photos & step-by-step styling tips on</span>
                <span class="underline decoration-[#E60023] decoration-2 underline-offset-4 font-bold">stylesdays.com</span>
              </div>
            </div>

            <!-- Standard HTML <a href="..."> — No JS Redirects -->
            <a 
              href="{canonical_url}" 
              target="_blank"
              rel="noopener"
              class="inline-flex items-center justify-center space-x-2 bg-[#E60023] hover:bg-[#c4001d] text-white font-bold text-sm px-6 py-3.5 rounded-xl shadow-sm transition shrink-0"
            >
              <span>Read Full Guide on stylesdays.com</span>
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
              </svg>
            </a>
          </div>
        </div>

        <!-- SUBSTANTIVE SECTION 1: Key Takeaways & Styling Highlights -->
        <section class="mb-8">
          <h2 class="font-serif-editorial text-xl font-bold text-stone-900 mb-4 flex items-center gap-2">
            <span>Key Styling Ideas & DIY Highlights Inside This Guide</span>
          </h2>
          <div class="grid grid-cols-1 gap-3">
            <div class="flex items-start gap-3.5 p-4 rounded-2xl bg-[#FAF8F5] border border-stone-200/80">
              <span class="w-6 h-6 rounded-full bg-stone-900 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">1</span>
              <p class="text-sm text-stone-700 leading-relaxed">Balanced Room Proportions: Anchor your layout with clean-lined furniture and intentional traffic flow suited for everyday living.</p>
            </div>
            <div class="flex items-start gap-3.5 p-4 rounded-2xl bg-[#FAF8F5] border border-stone-200/80">
              <span class="w-6 h-6 rounded-full bg-stone-900 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">2</span>
              <p class="text-sm text-stone-700 leading-relaxed">Layered Textures & Lighting: Combine natural wood finishes, breathable textiles, and warm ambient lighting for instant coziness.</p>
            </div>
            <div class="flex items-start gap-3.5 p-4 rounded-2xl bg-[#FAF8F5] border border-stone-200/80">
              <span class="w-6 h-6 rounded-full bg-stone-900 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">3</span>
              <p class="text-sm text-stone-700 leading-relaxed">Smart Customization & Upgrades: Elevate accessible base pieces with upgraded hardware, trim detailing, or modular organizers.</p>
            </div>
          </div>
        </section>

        <!-- SUBSTANTIVE SECTION 2: Editor's Curated Review Note -->
        <section class="mb-8 bg-stone-50 rounded-2xl p-5 sm:p-6 border-l-4 border-stone-900">
          <h3 class="text-xs font-bold uppercase tracking-wider text-stone-500 mb-2">
            stylesdays Design Note • Why It Works in Real-Life Homes
          </h3>
          <p class="text-stone-700 text-sm sm:text-base italic leading-relaxed font-serif-editorial">
            "We selected this guide from the stylesdays archive for its practical, budget-conscious approach to elevating everyday spaces."
          </p>
        </section>

        <!-- SECONDARY BOTTOM USER-INITIATED ANCHOR CTA -->
        <div class="pt-6 border-t border-stone-200/80 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div class="text-xs text-stone-500 text-center sm:text-left">
            <span>Direct stylesdays Permalink:</span>
            <span class="font-mono text-stone-700 break-all block sm:inline ml-0 sm:ml-1">{canonical_url}</span>
          </div>
          <a 
            href="{canonical_url}" 
            target="_blank"
            rel="noopener"
            class="w-full sm:w-auto text-center bg-stone-900 hover:bg-stone-800 text-white font-semibold text-xs px-5 py-3 rounded-xl transition shrink-0"
          >
            Continue to stylesdays.com →
          </a>
        </div>

      </div>
    </article>
  </main>
</body>
</html>
"""

print("Cleaning up old generated slug folders...")
for url in all_urls:
    clean_url = url if url.endswith('/') else url + '/'
    parts = [p for p in clean_url.split('/') if p]
    if len(parts) <= 1:
        continue
    slug = parts[-1]
    
    if os.path.exists(slug) and os.path.isdir(slug):
        shutil.rmtree(slug, ignore_errors=True)
        print(f"Deleted old folder: /{slug}")

print("Generating new pages...")
for url in all_urls:
    clean_url = url if url.endswith('/') else url + '/'
    parts = [p for p in clean_url.split('/') if p]
    if len(parts) <= 1:
        continue
    slug = parts[-1]
    
    wp_data = wp_posts_map.get(slug, {})
    title = wp_data.get("title") or slug.replace('-', ' ').title()
    image = wp_data.get("image") or "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?auto=format&fit=crop&w=1200&q=85"
    
    description = f"Explore our complete {title} guide on stylesdays.com. This curated feature breaks down practical room styling ideas, space-saving furniture layouts, and budget-friendly DIY upgrades tailored for real-life homes."
    
    # Auto-detect category
    category = "Home Decor"
    if "hack" in slug: category = "IKEA Hacks"
    elif "storage" in slug or "pax" in slug or "closet" in slug: category = "IKEA Storage"
    elif "daybed" in slug or "guest" in slug: category = "Guest Bedroom & Daybeds"
    elif "ikea" in slug and "bedroom" in slug: category = "IKEA Bedroom"
    
    os.makedirs(slug, exist_ok=True)
    file_path = os.path.join(slug, 'index.html')
    
    page_content = EDITORIAL_TEMPLATE.format(
        title=title,
        description=description,
        canonical_url=url,
        image=image,
        category=category
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(page_content)

print("All editorial hub pages successfully generated (distraction-free design)!")
