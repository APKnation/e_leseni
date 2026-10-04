import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

/**
 * Consistent "My Profile" entry point for every page header. One component,
 * one style — drop <app-profile-link /> wherever a header needs it.
 */
@Component({
  imports: [RouterLink],
  selector: 'app-profile-link',
  template: `
    <a
      routerLink="/profile"
      data-testid="profile-link"
      title="My Profile — personal details, NIDA number and password"
      class="btn-secondary inline-flex items-center gap-2 !py-2 text-sm whitespace-nowrap"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
      </svg>
      My Profile
    </a>
  `,
})
export class ProfileLink {}
