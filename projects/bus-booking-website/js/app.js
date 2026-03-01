/**
 * BusGo - Shared JavaScript Utilities
 * Shared data generators and helper functions used across all pages.
 */

// =====================================================
// BUS DATA GENERATOR
// =====================================================

const BUS_OPERATORS = [
  { name: 'TransNational Express', initials: 'TNE', types: ['AC Sleeper', 'AC Seater', 'Luxury'] },
  { name: 'Konsortium Express', initials: 'KE', types: ['AC Seater', 'Non-AC Seater'] },
  { name: 'Plusliner', initials: 'PL', types: ['Luxury', 'AC Sleeper'] },
  { name: 'StarMart Express', initials: 'SME', types: ['AC Seater', 'AC Sleeper'] },
  { name: 'Maraliner', initials: 'ML', types: ['Non-AC Seater', 'AC Seater'] },
  { name: 'Cityliner', initials: 'CL', types: ['AC Seater', 'Luxury'] },
  { name: 'Sani Express', initials: 'SE', types: ['AC Sleeper', 'AC Seater'] },
];

const AMENITIES_POOL = [
  '&#10052; A/C', '&#128264; WiFi', '&#128267; USB Charging', '&#127916; Entertainment',
  '&#127869; Snacks', '&#128704; Reclining Seats', '&#128700; Blanket', '&#128188; Power Outlet'
];

const ROUTE_DURATIONS = {
  default: { mins: 180, price: 30 },
  'Kuala Lumpur-Penang': { mins: 270, price: 35 },
  'Penang-Kuala Lumpur': { mins: 270, price: 35 },
  'Kuala Lumpur-Johor Bahru': { mins: 225, price: 28 },
  'Johor Bahru-Kuala Lumpur': { mins: 225, price: 28 },
  'Kuala Lumpur-Ipoh': { mins: 150, price: 22 },
  'Ipoh-Kuala Lumpur': { mins: 150, price: 22 },
  'Kuala Lumpur-Kota Bharu': { mins: 420, price: 45 },
  'Kota Bharu-Kuala Lumpur': { mins: 420, price: 45 },
  'Penang-Johor Bahru': { mins: 360, price: 55 },
  'Johor Bahru-Penang': { mins: 360, price: 55 },
  'Kuala Lumpur-Melaka': { mins: 120, price: 18 },
  'Melaka-Kuala Lumpur': { mins: 120, price: 18 },
  'Kuala Lumpur-Kuantan': { mins: 180, price: 30 },
  'Kuantan-Kuala Lumpur': { mins: 180, price: 30 },
  'Kuala Lumpur-Alor Setar': { mins: 330, price: 42 },
  'Alor Setar-Kuala Lumpur': { mins: 330, price: 42 },
};

const TYPE_PRICE_MULT = {
  'Non-AC Seater': 0.75,
  'AC Seater': 1.0,
  'AC Sleeper': 1.3,
  'Luxury': 1.7,
};

/**
 * Generates a list of bus objects for a given route and date.
 * Uses the route + date as a seed so results are consistent.
 */
function generateBuses(from, to, date, passengers) {
  const routeKey = `${from}-${to}`;
  const routeData = ROUTE_DURATIONS[routeKey] || ROUTE_DURATIONS['default'];
  const seed = hashCode(routeKey + date);

  const departures = ['06:00', '07:30', '09:00', '10:30', '12:00', '13:30', '15:00', '16:30', '18:00', '20:00', '22:00', '23:30'];
  const buses = [];

  departures.forEach((dep, idx) => {
    const opIdx = Math.abs(seed + idx * 7) % BUS_OPERATORS.length;
    const op = BUS_OPERATORS[opIdx];
    const typeIdx = Math.abs(seed + idx * 3) % op.types.length;
    const type = op.types[typeIdx];
    const priceMult = TYPE_PRICE_MULT[type] || 1;
    const variance = 1 + ((Math.abs(seed + idx) % 20) - 10) / 100; // ±10%
    const price = Math.round(routeData.price * priceMult * variance);

    const durationMins = routeData.mins + (Math.abs(seed + idx * 11) % 30) - 15;
    const duration = formatDuration(durationMins);
    const arrival = addMinutes(dep, durationMins);

    const seatsLeft = 2 + Math.abs(seed + idx * 13) % 28;

    // Pick 3-5 random amenities
    const amenityCount = 3 + Math.abs(seed + idx) % 3;
    const amenities = shuffleSeeded([...AMENITIES_POOL], seed + idx).slice(0, amenityCount);

    // Pre-book some seats
    const totalSeats = 40;
    const bookedCount = totalSeats - seatsLeft;
    const bookedSeats = [];
    for (let s = 0; s < bookedCount; s++) {
      let seatNum;
      do { seatNum = 1 + Math.abs(seed + idx * 17 + s * 3) % totalSeats; } while (bookedSeats.includes(seatNum));
      bookedSeats.push(seatNum);
    }

    buses.push({
      id: `bus_${idx}_${routeKey.replace(/\s/g, '_')}`,
      operator: op.name,
      operatorInitials: op.initials,
      type,
      departure: dep,
      arrival,
      duration,
      durationMins,
      price,
      seatsLeft,
      amenities,
      bookedSeats,
    });
  });

  return buses;
}

// =====================================================
// UTILITY FUNCTIONS
// =====================================================

function formatDuration(mins) {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${h}h ${String(m).padStart(2, '0')}m`;
}

function addMinutes(timeStr, mins) {
  const [h, m] = timeStr.split(':').map(Number);
  const total = h * 60 + m + mins;
  const nh = Math.floor(total / 60) % 24;
  const nm = total % 60;
  return `${String(nh).padStart(2, '0')}:${String(nm).padStart(2, '0')}`;
}

function hashCode(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i);
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

function shuffleSeeded(arr, seed) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.abs(hashCode(String(seed) + String(i))) % (i + 1);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function formatDate(d) {
  if (!d) return '';
  const dt = new Date(d + 'T00:00:00');
  return dt.toLocaleDateString('en-MY', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
}
