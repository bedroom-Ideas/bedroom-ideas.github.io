import os
import sys
import json
import urllib.request
import xml.etree.ElementTree as ET
import shutil
import random
from string import Template

sitemap_url = sys.argv[1] if len(sys.argv) > 1 else "https://stylesdays.com/sitemap_index.xml"
print(f"Fetching sitemap from: {sitemap_url}")

def fetch_data(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
    xml_data = fetch_data(url)
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

# 1. Gather all URLs from Sitemap
all_urls = parse_sitemap(sitemap_url)
print(f"Total unique URLs found: {len(all_urls)}")

# 2. Fetch Live WordPress Data (Titles, Excerpts, Images)
posts_data = {}
page = 1
per_page = 100

while True:
    print(f"Fetching WordPress REST API batch {page}...")
    wp_api_url = f"https://stylesdays.com/wp-json/wp/v2/posts?per_page={per_page}&page={page}&_embed=1"
    wp_data = fetch_data(wp_api_url)
    
    if not wp_data:
        break
        
    try:
        posts = json.loads(wp_data.decode('utf-8'))
        if not posts or len(posts) == 0:
            break
            
        for post in posts:
            slug = post.get('slug')
            if not slug:
                continue
            
            title = post.get('title', {}).get('rendered', slug.replace('-', ' ').title())
            excerpt = post.get('excerpt', {}).get('rendered', '')
            
            # Clean HTML tags from excerpt
            import re
            clean_excerpt = re.sub('<[^<]+>', '', excerpt).strip()
            if not clean_excerpt:
                clean_excerpt = f"Explore our complete {title} guide on stylesdays.com. This curated feature breaks down practical room styling ideas and layouts."
            
            # Extract featured image
            image_url = "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?auto=format&fit=crop&w=1200&q=85"
            try:
                embedded = post.get('_embedded', {})
                featured_media = embedded.get('wp:featuredmedia', [{}])[0]
                if 'source_url' in featured_media:
                    image_url = featured_media['source_url']
            except:
                pass

            posts_data[slug] = {
                'title': title,
                'description': clean_excerpt,
                'image': image_url,
                'canonical_url': f"https://stylesdays.com/{slug}/"
            }
            
        page += 1
    except Exception as e:
        print(f"Error parsing JSON on page {page}: {e}")
        break

print(f"Loaded {len(posts_data)} posts with metadata from WordPress REST API.")

# 3. HTML Template - Ultra Clean UX, Single Column Mobile-First
HIGH_CONVERTING_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>$title | StylesDays Editorial</title>
  <meta name="description" content="$description">
  
  <meta property="og:type" content="article">
  <meta property="og:title" content="$title">
  <meta property="og:description" content="$description">
  <meta property="og:image" content="$image">
  <meta property="og:site_name" content="StylesDays Editorial">
  <link rel="canonical" href="$canonical_url" />
  
  <script src="https://cdn.tailwindcss.com"></script>
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&display=swap" rel="stylesheet">
  
  <style>
    body { font-family: 'Inter', sans-serif; background-color: #f9fafb; color: #111827; }
    .font-serif-title { font-family: 'Playfair Display', Georgia, serif; }
    
    @keyframes subtlePulse {
      0%, 100% { transform: scale(1); box-shadow: 0 10px 25px -5px rgba(230, 0, 35, 0.4); }
      50% { transform: scale(1.02); box-shadow: 0 18px 30px -5px rgba(230, 0, 35, 0.6); }
    }
    .pinterest-cta-pulse { animation: subtlePulse 2.5s ease-in-out infinite; }
    .pinterest-cta-pulse:hover { animation: none; transform: scale(1.02); }
  </style>
</head>
<body class="min-h-screen flex flex-col selection:bg-[#E60023] selection:text-white">

  <!-- Clean Minimal Header -->
  <header class="w-full bg-white/90 backdrop-blur-md border-b border-gray-200 sticky top-0 z-40 shadow-sm">
    <div class="max-w-3xl mx-auto px-5 py-3 flex items-center justify-between">
      <div class="font-serif-title text-xl font-bold tracking-tight text-gray-900">StylesDays</div>
      <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-green-500"></span> Official Hub
      </div>
    </div>
  </header>

  <main class="max-w-3xl w-full mx-auto px-5 py-8 flex-grow">
    
    <!-- Hero Image -->
    <div class="relative w-full aspect-[16/10] sm:aspect-[16/9] rounded-2xl overflow-hidden shadow-sm mb-6 cursor-pointer group" onclick="window.location.href='$canonical_url'">
      <img src="$image" alt="$title" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105">
      <div class="absolute top-4 left-4 bg-white/95 backdrop-blur-md text-gray-900 text-xs font-bold uppercase tracking-wider px-3 py-1.5 rounded-full shadow-sm">
        $category
      </div>
    </div>

    <!-- Title & Intro -->
    <div class="mb-8">
      <h1 class="font-serif-title text-3xl sm:text-4xl font-bold text-gray-900 leading-tight mb-4 hover:text-[#E60023] transition">
        <a href="$canonical_url">$title</a>
      </h1>
      <p class="text-gray-600 text-base sm:text-lg leading-relaxed">
        $description
      </p>
    </div>

    <!-- MAIN CONVERSION ZONE (Frictionless, High Contrast) -->
    <div class="bg-white rounded-3xl shadow-sm border border-gray-200 p-6 sm:p-8 mb-10 text-center">
      <p class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-5">Read the full illustrated guide</p>
      
      <a href="$canonical_url" target="_blank" rel="noopener" class="pinterest-cta-pulse w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-[#E60023] text-white text-lg font-bold py-4 px-10 rounded-2xl shadow-lg transition duration-150">
        <span>Continue to StylesDays</span>
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
        </svg>
      </a>

      <div class="flex flex-wrap items-center justify-center gap-5 mt-6 text-xs text-gray-500 font-medium">
        <div class="flex items-center gap-1.5">
          <svg class="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>
          <span>Safe Link</span>
        </div>
        <div class="flex items-center gap-1.5">
          <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
          <span>Fast Loading</span>
        </div>
      </div>
    </div>

    <!-- Muted Compliance Data (Required to avoid Pinterest 'Thin Content' penalty) -->
    <div class="grid sm:grid-cols-2 gap-4 mb-12">
      <div class="bg-gray-100/50 rounded-2xl p-5 border border-gray-200/50">
        <h3 class="font-bold text-sm text-gray-800 mb-3">Key Highlights</h3>
        <ul class="text-sm text-gray-600 space-y-2">
          <li class="flex items-start gap-2"><span class="text-gray-400 mt-0.5">•</span> Intentional styling for real-life spaces.</li>
          <li class="flex items-start gap-2"><span class="text-gray-400 mt-0.5">•</span> Layered textures & optimal lighting.</li>
        </ul>
      </div>
      <div class="bg-gray-100/50 rounded-2xl p-5 border border-gray-200/50">
        <h3 class="font-bold text-sm text-gray-800 mb-3">Project Prep</h3>
        <ul class="text-sm text-gray-600 space-y-2">
          <li class="flex items-start gap-2"><input type="checkbox" checked disabled class="mt-1 rounded text-gray-400"> Review photos on StylesDays</li>
          <li class="flex items-start gap-2"><input type="checkbox" checked disabled class="mt-1 rounded text-gray-400"> Save to Pinterest board</li>
        </ul>
      </div>
    </div>

    <!-- Related Posts -->
    <div class="pt-8 border-t border-gray-200">
      <h2 class="font-serif-title text-2xl font-bold text-gray-900 mb-6">More Featured Guides</h2>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
        $related_posts_html
      </div>
    </div>

  </main>
  
  <footer class="w-full border-t border-gray-200 bg-white py-6 mt-auto text-center text-xs text-gray-400">
    <p>&copy; 2026 StylesDays Editorial Hub.</p>
  </footer>
</body>
</html>
""")

def get_related_posts_html(current_slug, posts_data):
    """Pick 3 random posts (excluding the current one) to display in the bottom grid."""
    available_slugs = [s for s in posts_data.keys() if s != current_slug]
    if not available_slugs:
        return ""
        
    selected_slugs = random.sample(available_slugs, min(3, len(available_slugs)))
    cards_html = ""
    
    for s in selected_slugs:
        p = posts_data[s]
        img = p.get('image', 'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=800&q=80')
        title = p.get('title', 'StylesDays Guide')
        url = p.get('canonical_url', f'https://stylesdays.com/{s}/')
        
        cat = "Home Decor"
        if "hack" in s: cat = "IKEA Hacks"
        elif "storage" in s or "pax" in s: cat = "IKEA Storage"
        elif "bedroom" in s: cat = "IKEA Bedroom"
        
        card = f"""
        <a href="{url}" target="_blank" rel="noopener" class="block bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition group">
          <div class="aspect-[16/10] overflow-hidden relative">
            <img src="{img}" alt="{title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">
            <span class="absolute top-2 left-2 bg-white/90 backdrop-blur-sm text-gray-900 text-[9px] font-bold uppercase px-2 py-1 rounded-full">
              {cat}
            </span>
          </div>
          <div class="p-4">
            <h3 class="font-serif-title text-sm font-bold text-gray-900 group-hover:text-[#E60023] transition-colors leading-snug line-clamp-2">
              {title}
            </h3>
          </div>
        </a>
        """
        cards_html += card
        
    return cards_html

print(f"\\nCleaning up old generated slug folders and generating {len(posts_data)} new pages...")

for slug, data in posts_data.items():
    category = "Home Decor"
    if "hack" in slug:
        category = "IKEA Hacks"
    elif "storage" in slug or "pax" in slug or "closet" in slug:
        category = "IKEA Storage"
    elif "daybed" in slug or "guest" in slug:
        category = "Guest Bedroom & Daybeds"
    elif "bedroom" in slug:
        category = "Bedroom Design"

    related_posts_html = get_related_posts_html(slug, posts_data)
    
    shutil.rmtree(slug, ignore_errors=True)
    os.makedirs(slug, exist_ok=True)
    file_path = os.path.join(slug, 'index.html')
    
    page_content = HIGH_CONVERTING_TEMPLATE.safe_substitute(
        title=data['title'],
        description=data['description'],
        canonical_url=data['canonical_url'],
        image=data['image'],
        category=category,
        related_posts_html=related_posts_html
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(page_content)

print("\\nAll highly-converting editorial hub pages successfully generated!")
