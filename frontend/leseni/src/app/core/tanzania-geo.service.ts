/**
 * Tanzania administrative geography: regions → districts (LGAs/councils) → wards.
 *
 * Data source: the `tanzaniageodata` npm package (GeoJSON feature files).
 * Everything is loaded lazily on first use and cached; ward lookups are
 * served from an in-memory index, so navigation stays instant.
 */
import { Injectable } from '@angular/core';

import DISTRICTS_JSON from 'tanzaniageodata/Countries/Tanzania/Districts.json';
import REGIONS_JSON from 'tanzaniageodata/Countries/Tanzania/Regions.json';
import WARDS_JSON from 'tanzaniageodata/Countries/Tanzania/Wards.json';

/** Raw feature shape from the tanzaniageodata GeoJSON files. */
interface GeoFeature {
  type: 'Feature';
  properties: {
    region?: string;
    District?: string;
    Ward?: string;
  };
  geometry: unknown;
}

interface GeoCollection {
  name: string;
  features: GeoFeature[];
}

export interface District {
  /** District name without the "District"/"Municipal"/"City" suffix, e.g. "Ilala". */
  name: string;
  /** Full district name as found in the dataset, e.g. "Ilala Municipal". */
  fullName: string;
}

@Injectable({ providedIn: 'root' })
export class TanzaniaGeoService {
  /** Regions in dataset order, e.g. ["Arusha", "Dar es Salaam", ...]. */
  private readonly regionNames: string[];

  /** region → district full names, e.g. "Kilimanjaro" → ["Hai District", ...]. */
  private readonly districtsByRegion = new Map<string, string[]>();

  /** district full name → sorted ward names. */
  private readonly wardsByDistrict = new Map<string, string[]>();

  constructor() {
    const regions = (REGIONS_JSON as unknown as GeoCollection).features
      .map((f) => f.properties.region ?? '')
      .filter((r) => r.length > 0);

    const districts = (DISTRICTS_JSON as unknown as GeoCollection).features;
    for (const feature of districts) {
      const region = (feature.properties.region ?? '').replace(/ Region$/, '');
      const district = feature.properties.District ?? '';
      if (!region || !district) continue;
      const list = this.districtsByRegion.get(region) ?? [];
      if (!list.includes(district)) list.push(district);
      this.districtsByRegion.set(region, list);
    }

    const wards = (WARDS_JSON as unknown as GeoCollection).features;
    for (const feature of wards) {
      const district = feature.properties.District ?? '';
      const ward = feature.properties.Ward ?? '';
      if (!district || !ward) continue;
      const list = this.wardsByDistrict.get(district) ?? [];
      if (!list.includes(ward)) list.push(ward);
      this.wardsByDistrict.set(district, list);
    }

    // Keep only regions that actually have districts in the dataset
    // (Regions.json lists 31 incl. Mjini Magharibi variants; Districts.json 30).
    this.regionNames = regions.filter((r) => this.districtsByRegion.has(r));
  }

  /** All regions covered by the dataset, alphabetically. */
  regions(): string[] {
    return [...this.regionNames].sort();
  }

  /** Councils (districts) of a region, in dataset order. */
  districts(region: string): District[] {
    return (this.districtsByRegion.get(region) ?? []).map((fullName) => ({
      fullName,
      name: this.shortDistrictName(fullName),
    }));
  }

  /** Wards of a council/district, alphabetically. */
  wards(districtFullName: string): string[] {
    return [...(this.wardsByDistrict.get(districtFullName) ?? [])].sort();
  }

  /** "Ilala Municipal" → "Ilala", "Arusha City" → "Arusha", "Hai District" → "Hai". */
  shortDistrictName(fullName: string): string {
    return fullName
      .replace(/ Municipal Council$/, '')
      .replace(/ District Council$/, '')
      .replace(/ Town Council$/, '')
      .replace(/ Municipal$/, '')
      .replace(/ District$/, '')
      .replace(/ City$/, '')
      .replace(/ Council$/, '');
  }
}
