import { IndicatorStatus, StratumType } from '../wetland/types';
import { PlotRecord, ProjectRecord, ReferenceTaxonRecord, VegetationTaxonRecord } from './schema';

export const REFERENCE_PLANTS: ReferenceTaxonRecord[] = [
  // Trees
  {
    id: 'tax-1',
    symbol: 'ACRU',
    scientific_name: 'Acer rubrum',
    common_name: 'Red Maple',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-2',
    symbol: 'LIST2',
    scientific_name: 'Liquidambar styraciflua',
    common_name: 'Sweetgum',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-3',
    symbol: 'PITA',
    scientific_name: 'Pinus taeda',
    common_name: 'Loblolly Pine',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-4',
    symbol: 'TUDI2',
    scientific_name: 'Taxodium distichum',
    common_name: 'Bald Cypress',
    emp_indicator: 'OBL',
    agcp_indicator: 'OBL',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-5',
    symbol: 'NYSY',
    scientific_name: 'Nyssa sylvatica',
    common_name: 'Blackgum',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-6',
    symbol: 'NYBI',
    scientific_name: 'Nyssa biflora',
    common_name: 'Swamp Tupelo',
    emp_indicator: 'OBL',
    agcp_indicator: 'OBL',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-7',
    symbol: 'QUNI',
    scientific_name: 'Quercus nigra',
    common_name: 'Water Oak',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-8',
    symbol: 'QUFA',
    scientific_name: 'Quercus falcata',
    common_name: 'Southern Red Oak',
    emp_indicator: 'FACU',
    agcp_indicator: 'FACU',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-9',
    symbol: 'FAGR',
    scientific_name: 'Fagus grandifolia',
    common_name: 'American Beech',
    emp_indicator: 'FACU',
    agcp_indicator: 'FACU',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-10',
    symbol: 'LITU',
    scientific_name: 'Liriodendron tulipifera',
    common_name: 'Tuliptree',
    emp_indicator: 'FACU',
    agcp_indicator: 'FACU',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-11',
    symbol: 'PLOC',
    scientific_name: 'Platanus occidentalis',
    common_name: 'American Sycamore',
    emp_indicator: 'FACW',
    agcp_indicator: 'FACW',
    typical_stratum: 'tree'
  },
  {
    id: 'tax-12',
    symbol: 'FRPE',
    scientific_name: 'Fraxinus pennsylvanica',
    common_name: 'Green Ash',
    emp_indicator: 'FACW',
    agcp_indicator: 'FACW',
    typical_stratum: 'tree'
  },

  // Sapling / Shrub
  {
    id: 'tax-13',
    symbol: 'ALSE2',
    scientific_name: 'Alnus serrulata',
    common_name: 'Hazel Alder',
    emp_indicator: 'OBL',
    agcp_indicator: 'FACW',
    typical_stratum: 'sapling_shrub'
  },
  {
    id: 'tax-14',
    symbol: 'CEOC2',
    scientific_name: 'Cephalanthus occidentalis',
    common_name: 'Common Buttonbush',
    emp_indicator: 'OBL',
    agcp_indicator: 'OBL',
    typical_stratum: 'sapling_shrub'
  },
  {
    id: 'tax-15',
    symbol: 'ILVO',
    scientific_name: 'Ilex vomitoria',
    common_name: 'Yaupon Holly',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'sapling_shrub'
  },
  {
    id: 'tax-16',
    symbol: 'ILGL',
    scientific_name: 'Ilex glabra',
    common_name: 'Inkberry',
    emp_indicator: 'FACW',
    agcp_indicator: 'FACW',
    typical_stratum: 'sapling_shrub'
  },
  {
    id: 'tax-17',
    symbol: 'COAM2',
    scientific_name: 'Cornus amomum',
    common_name: 'Silky Dogwood',
    emp_indicator: 'FACW',
    agcp_indicator: 'FACW',
    typical_stratum: 'sapling_shrub'
  },
  {
    id: 'tax-18',
    symbol: 'MOCE2',
    scientific_name: 'Morella cerifera',
    common_name: 'Wax Myrtle',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'sapling_shrub'
  },
  {
    id: 'tax-19',
    symbol: 'VAPR',
    scientific_name: 'Vaccinium formosum',
    common_name: 'Swamp Highbush Blueberry',
    emp_indicator: 'FACW',
    agcp_indicator: 'FACW',
    typical_stratum: 'sapling_shrub'
  },
  {
    id: 'tax-20',
    symbol: 'LILU',
    scientific_name: 'Ligustrum sinense',
    common_name: 'Chinese Privet',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'sapling_shrub'
  },

  // Herbs
  {
    id: 'tax-21',
    symbol: 'TYLA',
    scientific_name: 'Typha latifolia',
    common_name: 'Broadleaf Cattail',
    emp_indicator: 'OBL',
    agcp_indicator: 'OBL',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-22',
    symbol: 'CALU4',
    scientific_name: 'Carex lurida',
    common_name: 'Shallow Sedge',
    emp_indicator: 'OBL',
    agcp_indicator: 'OBL',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-23',
    symbol: 'CAST4',
    scientific_name: 'Carex stricta',
    common_name: 'Upright Sedge',
    emp_indicator: 'OBL',
    agcp_indicator: 'OBL',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-24',
    symbol: 'JUEF',
    scientific_name: 'Juncus effusus',
    common_name: 'Common Rush',
    emp_indicator: 'FACW',
    agcp_indicator: 'FACW',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-25',
    symbol: 'BOCY',
    scientific_name: 'Boehmeria cylindrica',
    common_name: 'Smallspike False Nettle',
    emp_indicator: 'OBL',
    agcp_indicator: 'FACW',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-26',
    symbol: 'MIVI',
    scientific_name: 'Microstegium vimineum',
    common_name: 'Japanese Stiltgrass',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-27',
    symbol: 'OSCI',
    scientific_name: 'Osmundastrum cinnamomeum',
    common_name: 'Cinnamon Fern',
    emp_indicator: 'FACW',
    agcp_indicator: 'FACW',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-28',
    symbol: 'ONSE',
    scientific_name: 'Onoclea sensibilis',
    common_name: 'Sensitive Fern',
    emp_indicator: 'FACW',
    agcp_indicator: 'FACW',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-29',
    symbol: 'SACY5',
    scientific_name: 'Sagittaria latifolia',
    common_name: 'Broadleaf Arrowhead',
    emp_indicator: 'OBL',
    agcp_indicator: 'OBL',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-30',
    symbol: 'POHY4',
    scientific_name: 'Persicaria hydropiperoides',
    common_name: 'Swamp Smartweed',
    emp_indicator: 'OBL',
    agcp_indicator: 'OBL',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-31',
    symbol: 'PODO4',
    scientific_name: 'Podophyllum peltatum',
    common_name: 'Mayapple',
    emp_indicator: 'FACU',
    agcp_indicator: 'FACU',
    typical_stratum: 'herb'
  },
  {
    id: 'tax-32',
    symbol: 'SOAL',
    scientific_name: 'Solidago altissima',
    common_name: 'Late Goldenrod',
    emp_indicator: 'FACU',
    agcp_indicator: 'FACU',
    typical_stratum: 'herb'
  },

  // Woody Vines
  {
    id: 'tax-33',
    symbol: 'TORA2',
    scientific_name: 'Toxicodendron radicans',
    common_name: 'Eastern Poison Ivy',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'woody_vine'
  },
  {
    id: 'tax-34',
    symbol: 'SMRO',
    scientific_name: 'Smilax rotundifolia',
    common_name: 'Roundleaf Greenbrier',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'woody_vine'
  },
  {
    id: 'tax-35',
    symbol: 'SMGL',
    scientific_name: 'Smilax glauca',
    common_name: 'Cat Greenbrier',
    emp_indicator: 'FACU',
    agcp_indicator: 'FAC',
    typical_stratum: 'woody_vine'
  },
  {
    id: 'tax-36',
    symbol: 'PAQU2',
    scientific_name: 'Parthenocissus quinquefolia',
    common_name: 'Virginia Creeper',
    emp_indicator: 'FACU',
    agcp_indicator: 'FAC',
    typical_stratum: 'woody_vine'
  },
  {
    id: 'tax-37',
    symbol: 'LOJA',
    scientific_name: 'Lonicera japonica',
    common_name: 'Japanese Honeysuckle',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'woody_vine'
  },
  {
    id: 'tax-38',
    symbol: 'VIRO3',
    scientific_name: 'Vitis rotundifolia',
    common_name: 'Muscadine',
    emp_indicator: 'FAC',
    agcp_indicator: 'FAC',
    typical_stratum: 'woody_vine'
  }
];

export const SEED_PROJECT: ProjectRecord = {
  id: 'proj-demo-1',
  client_project_code: 'PLST-2026-NC01',
  project_name: 'Neuse River Basin Wetland Mitigation & Delineation',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  sync_status: 'clean'
};

export const SEED_PLOT: PlotRecord = {
  id: 'plot-demo-1',
  project_id: 'proj-demo-1',
  plot_name: 'SP-01-WETLAND-FOREST',
  latitude: 35.7796,
  longitude: -78.6382,
  datum: 'WGS84',
  region: 'EMP',
  determination_result: 'IN_PROGRESS',
  is_deleted: false,
  sync_status: 'clean',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
};

export const SEED_TAXA: VegetationTaxonRecord[] = [
  // Tree Stratum
  {
    id: 'seed-tax-1',
    plot_id: 'plot-demo-1',
    stratum_id: 'tree',
    usda_symbol: 'ACRU',
    taxon: 'Acer rubrum',
    common_name: 'Red Maple',
    percent_cover: 40,
    indicator_status: 'FAC',
    is_deleted: false,
    sync_status: 'clean',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'seed-tax-2',
    plot_id: 'plot-demo-1',
    stratum_id: 'tree',
    usda_symbol: 'LIST2',
    taxon: 'Liquidambar styraciflua',
    common_name: 'Sweetgum',
    percent_cover: 25,
    indicator_status: 'FAC',
    is_deleted: false,
    sync_status: 'clean',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'seed-tax-3',
    plot_id: 'plot-demo-1',
    stratum_id: 'tree',
    usda_symbol: 'LITU',
    taxon: 'Liriodendron tulipifera',
    common_name: 'Tuliptree',
    percent_cover: 15,
    indicator_status: 'FACU',
    is_deleted: false,
    sync_status: 'clean',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },

  // Sapling / Shrub
  {
    id: 'seed-tax-4',
    plot_id: 'plot-demo-1',
    stratum_id: 'sapling_shrub',
    usda_symbol: 'ALSE2',
    taxon: 'Alnus serrulata',
    common_name: 'Hazel Alder',
    percent_cover: 35,
    indicator_status: 'OBL',
    is_deleted: false,
    sync_status: 'clean',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'seed-tax-5',
    plot_id: 'plot-demo-1',
    stratum_id: 'sapling_shrub',
    usda_symbol: 'COAM2',
    taxon: 'Cornus amomum',
    common_name: 'Silky Dogwood',
    percent_cover: 20,
    indicator_status: 'FACW',
    is_deleted: false,
    sync_status: 'clean',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },

  // Herb Stratum
  {
    id: 'seed-tax-6',
    plot_id: 'plot-demo-1',
    stratum_id: 'herb',
    usda_symbol: 'CALU4',
    taxon: 'Carex lurida',
    common_name: 'Shallow Sedge',
    percent_cover: 45,
    indicator_status: 'OBL',
    is_deleted: false,
    sync_status: 'clean',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'seed-tax-7',
    plot_id: 'plot-demo-1',
    stratum_id: 'herb',
    usda_symbol: 'BOCY',
    taxon: 'Boehmeria cylindrica',
    common_name: 'Smallspike False Nettle',
    percent_cover: 25,
    indicator_status: 'OBL',
    is_deleted: false,
    sync_status: 'clean',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'seed-tax-8',
    plot_id: 'plot-demo-1',
    stratum_id: 'herb',
    usda_symbol: 'MIVI',
    taxon: 'Microstegium vimineum',
    common_name: 'Japanese Stiltgrass',
    percent_cover: 10,
    indicator_status: 'FAC',
    is_deleted: false,
    sync_status: 'clean',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },

  // Woody Vine
  {
    id: 'seed-tax-9',
    plot_id: 'plot-demo-1',
    stratum_id: 'woody_vine',
    usda_symbol: 'TORA2',
    taxon: 'Toxicodendron radicans',
    common_name: 'Eastern Poison Ivy',
    percent_cover: 20,
    indicator_status: 'FAC',
    is_deleted: false,
    sync_status: 'clean',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];
