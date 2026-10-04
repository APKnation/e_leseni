export const API_BASE_URL = 'http://localhost:8000/api';

/** Server root (no /api) — for non-API endpoints like the USSD gateway. */
export const SERVER_BASE_URL = API_BASE_URL.replace(/\/api\/?$/, '');
