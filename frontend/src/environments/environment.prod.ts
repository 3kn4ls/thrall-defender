export const environment = {
  production: true,
  apiUrl: '/thrall-defender/api',
  wsUrl: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/thrall-defender/ws`
};
