import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID } from '@angular/core';

import { AuthService, UserRole } from './auth.service';

/**
 * Guards are evaluated during the server render of the initial document too,
 * where sessionStorage is invisible — blindly redirecting there would bounce
 * every hard page load to /login even for logged-in users (the session exists
 * only in the browser). So on the server we always allow the render; on the
 * client the guard runs again and redirects after that, once storage is
 * readable — including in the dev server, which SSRs every request.
 */
function clientOnlyGuard(
  guard: (auth: AuthService, router: Router, stateUrl: string) => true | ReturnType<Router['createUrlTree']>,
  stateUrl: string,
): true | ReturnType<Router['createUrlTree']> {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!isPlatformBrowser(inject(PLATFORM_ID))) return true;
  return guard(auth, router, stateUrl);
}

function requireRoles(roles: UserRole[], stateUrl: string, fallback = '/dashboard') {
  return clientOnlyGuard((auth, router, url) => {
    if (!auth.isLoggedIn()) {
      return router.createUrlTree(['/login'], { queryParams: { returnUrl: url } });
    }
    if (auth.hasRole(...roles)) return true;
    return router.createUrlTree([auth.homeRoute()]);
  }, stateUrl);
}

/** Requires a logged-in user; remembers where the user was heading. */
export const authGuard: CanActivateFn = (_route, state) =>
  clientOnlyGuard((auth, router, url) => {
    if (auth.isLoggedIn()) return true;
    return router.createUrlTree(['/login'], { queryParams: { returnUrl: url } });
  }, state.url);

/** Any LGA staff role (OFFICER, INSPECTOR, APPROVER, ADMIN). */
export const staffGuard: CanActivateFn = (_route, state) =>
  requireRoles(['OFFICER', 'INSPECTOR', 'APPROVER', 'ADMIN'], state.url);

/** Role-specific guards for the per-role staff pages. */
export const officerGuard: CanActivateFn = (_route, state) =>
  requireRoles(['OFFICER', 'ADMIN'], state.url);

export const inspectorGuard: CanActivateFn = (_route, state) =>
  requireRoles(['INSPECTOR', 'ADMIN'], state.url);

export const approverGuard: CanActivateFn = (_route, state) =>
  requireRoles(['APPROVER', 'ADMIN'], state.url);

export const adminGuard: CanActivateFn = (_route, state) =>
  requireRoles(['ADMIN'], state.url);
