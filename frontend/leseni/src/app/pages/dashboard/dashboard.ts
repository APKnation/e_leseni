import { Component, inject } from '@angular/core';

import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.html',
})
export class Dashboard {
  protected readonly auth = inject(AuthService);
  protected readonly user = () => this.auth.currentUser();
}
