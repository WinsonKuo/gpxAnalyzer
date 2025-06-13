import xml.etree.ElementTree as ET
import math
import argparse
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rc('font', family='STHeiti')

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def parse_gpx(path):
    tree = ET.parse(path)
    root = tree.getroot()

    ns = {
        'default': 'http://www.topografix.com/GPX/1/1'
    }

    trkpts = []
    for trkpt in root.findall('.//default:trkpt', ns):
        lat = float(trkpt.attrib['lat'])
        lon = float(trkpt.attrib['lon'])
        ele_elem = trkpt.find('default:ele', ns)
        ele = float(ele_elem.text) if ele_elem is not None else 0.0
        trkpts.append((lat, lon, ele))

    wpts = []
    for wpt in root.findall('default:wpt', ns):
        lat = float(wpt.attrib['lat'])
        lon = float(wpt.attrib['lon'])
        name_elem = wpt.find('default:name', ns)
        name = name_elem.text if name_elem is not None else ''
        wpts.append((lat, lon, name))

    return trkpts, wpts


def compute_distances(trkpts):
    dists = [0.0]
    for i in range(1, len(trkpts)):
        lat1, lon1, _ = trkpts[i-1]
        lat2, lon2, _ = trkpts[i]
        d = haversine(lat1, lon1, lat2, lon2)
        dists.append(dists[-1] + d)
    return dists


def interpolate_elevation(distance, dists, eles):
    for i in range(1, len(dists)):
        if distance <= dists[i]:
            d0, d1 = dists[i-1], dists[i]
            e0, e1 = eles[i-1], eles[i]
            if d1 == d0:
                return e1
            ratio = (distance - d0) / (d1 - d0)
            return e0 + ratio * (e1 - e0)
    return eles[-1]


def slope_to_color(slope):
    pct = slope * 100
    if pct < 0:
        return 'blue'
    elif pct < 3:
        return 'darkgreen'
    elif pct < 6:
        return 'limegreen'
    elif pct < 10:
        return 'yellow'
    elif pct < 15:
        return 'orange'
    else:
        return 'red'


def segment_slopes(dists, eles, segment=100.0):
    total = dists[-1]
    boundaries = [i for i in range(0, int(total // segment) * int(segment) + int(segment) + 1, int(segment))]
    if boundaries[-1] < total:
        boundaries.append(total)

    segments = []
    for i in range(len(boundaries)-1):
        start_d = boundaries[i]
        end_d = boundaries[i+1]
        start_e = interpolate_elevation(start_d, dists, eles)
        end_e = interpolate_elevation(end_d, dists, eles)
        seg_dist = end_d - start_d
        slope = (end_e - start_e) / seg_dist if seg_dist != 0 else 0
        segments.append((start_d, end_d, slope))
    return segments


def waypoint_positions(wpts, trkpts, dists):
    positions = []
    for lat, lon, name in wpts:
        # find nearest track point
        min_idx = 0
        min_dist = float('inf')
        for i, (tlat, tlon, _) in enumerate(trkpts):
            d = haversine(lat, lon, tlat, tlon)
            if d < min_dist:
                min_dist = d
                min_idx = i
        positions.append((dists[min_idx], name))
    return positions


def plot_profile(trkpts, wpts):
    dists = compute_distances(trkpts)
    eles = [pt[2] for pt in trkpts]

    segments = segment_slopes(dists, eles)

    fig, ax = plt.subplots(figsize=(10, 6))

    # draw overall elevation profile
    ax.plot(dists, eles, color='black', linewidth=1)

    # fill segments with colors based on average slope
    for start_d, end_d, slope in segments:
        seg_d = [start_d]
        seg_e = [interpolate_elevation(start_d, dists, eles)]
        for d, e in zip(dists, eles):
            if start_d < d < end_d:
                seg_d.append(d)
                seg_e.append(e)
        seg_d.append(end_d)
        seg_e.append(interpolate_elevation(end_d, dists, eles))
        color = slope_to_color(slope)
        ax.fill_between(seg_d, seg_e, [0]*len(seg_d), color=color, alpha=0.3)

    # mark waypoints
    positions = waypoint_positions(wpts, trkpts, dists)
    for dist_pos, name in positions:
        ele = interpolate_elevation(dist_pos, dists, eles)
        ax.scatter([dist_pos], [ele], color='blue')
        ax.text(dist_pos, ele + 5, name, rotation=45, ha='right', va='bottom')

    ax.set_xlabel('Distance (m)')
    ax.set_ylabel('Elevation (m)')
    ax.set_title('Elevation Profile with Slope Coloring')
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Plot GPX elevation profile with slope coloring.')
    parser.add_argument('gpx_file', help='Path to GPX file')
    args = parser.parse_args()

    trkpts, wpts = parse_gpx(args.gpx_file)
    if not trkpts:
        print('No track points found.')
        return
    plot_profile(trkpts, wpts)


if __name__ == '__main__':
    main()
