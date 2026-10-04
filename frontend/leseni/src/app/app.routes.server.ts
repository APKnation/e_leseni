import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  { path: 'verify', renderMode: RenderMode.Server },
  { path: 'verify/:token', renderMode: RenderMode.Server },

  // Authenticated areas render client-side only. The session lives in
  // sessionStorage, which the server cannot see, so letting the SSR engine
  // render these routes would evaluate the auth guards server-side and
  // bounce every hard reload / F5 to /login?returnUrl=… The client boots,
  // restores the session and runs the guards in the browser instead.
  { path: 'dashboard', renderMode: RenderMode.Client },
  { path: 'businesses', renderMode: RenderMode.Client },
  { path: 'apply', renderMode: RenderMode.Client },
  { path: 'profile', renderMode: RenderMode.Client },
  { path: 'ussd-demo', renderMode: RenderMode.Client },
  { path: 'staff', renderMode: RenderMode.Client },
  { path: 'staff/**', renderMode: RenderMode.Client },

  {
    path: '**',
    renderMode: RenderMode.Prerender
  }
];
