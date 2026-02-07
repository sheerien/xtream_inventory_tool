# core/extractor.py

from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 8  # cloud-safe

def extract_series_inventory(host, api, progress_cb=None):
    rows = []

    categories = api.get_series_categories()

    all_series = []
    for cat in categories:
        series_list = api.get_series(cat["category_id"])
        for s in series_list:
            s["_category_name"] = cat["category_name"]
        all_series.extend(series_list)

    series_ids = [s["series_id"] for s in all_series]

    infos = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(api.get_series_info, sid): sid
            for sid in series_ids
        }

        completed = 0
        total = len(series_ids)

        for future in as_completed(future_map):
            sid = future_map[future]
            infos[sid] = future.result() or {}

            completed += 1
            if progress_cb:
                progress_cb(completed, total)

    for s in all_series:
        info = infos.get(s["series_id"], {})
        episodes = info.get("episodes", {})

        for season, eps in episodes.items():
            rows.append({
                "server": host,
                "category_name": s["_category_name"],
                "series_id": s["series_id"],
                "series_name": s["name"],
                "season": int(season),
                "episodes_count": len(eps),
            })

    return rows
