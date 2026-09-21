import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService, UserRole } from './auth.service';

function requireRoles(roles: UserRole[], stateUrl: string, fallback = '/dashboard') {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.isLoggedIn()) {
    return router.createUrlTree(['/login'], { queryParams: { returnUrl: stateUrl } });
  }
  if (auth.hasRole(...roles)) return true;
  return router.createUrlTree([auth.homeRoute()]);
}

/** Requires a logged-in user; remembers where the user was heading. */
export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isLoggedIn()) return true;
  return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};

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
