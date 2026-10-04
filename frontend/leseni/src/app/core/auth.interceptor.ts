import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, finalize, map, share, switchMap, throwError } from 'rxjs';

import { AuthService } from './auth.service';

/**
 * Attaches the JWT access token. On 401 it tries one silent refresh
 * (POST /auth/refresh/ — the backend rotates tokens) and replays the original
 * request with the fresh token; only when that fails does it log the user out.
 * Concurrent 401s share a single in-flight refresh so a burst of parallel API
 * calls triggers exactly one backend refresh.
 */
let refreshInFlight: import('rxjs').Observable<string> | null = null;

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  const attach = (token: string | null) =>
    token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  const forceLogout = () => {
    auth.logout();
    void router.navigate(['/login']);
  };

  return next(attach(auth.accessToken)).pipe(
    catchError((error: unknown) => {
      if (!(error instanceof HttpErrorResponse) || error.status !== 401) {
        return throwError(() => error);
      }
      // Never try to refresh the auth endpoints themselves (avoids loops).
      if (req.url.includes('/auth/login/') || req.url.includes('/auth/refresh/')) {
        forceLogout();
        return throwError(() => error);
      }
      if (!auth.refreshToken) {
        forceLogout();
        return throwError(() => error);
      }

      refreshInFlight ??= auth.refresh().pipe(
        map(({ access, refresh }) => {
          auth.setTokens(access, refresh);
          return access;
        }),
        finalize(() => {
          refreshInFlight = null;
        }),
        share(),
      );

      return refreshInFlight.pipe(
        switchMap((access) => next(attach(access))),
        catchError((refreshError: unknown) => {
          forceLogout();
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
