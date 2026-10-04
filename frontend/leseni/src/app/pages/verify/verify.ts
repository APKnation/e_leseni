import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../core/api.service';

@Component({
  imports: [CommonModule, FormsModule],
  selector: 'app-verify',
  templateUrl: './verify.html',
})
export class Verify implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly api = inject(ApiService);

  protected loading = signal(false);
  protected error = signal<string | null>(null);
  protected result = signal<any>(null);

  /** True when a QR token was provided in the URL path. */
  protected hasToken = signal(false);

  /** Token typed manually in the input form. */
  protected manualToken = signal('');

  /** Formatted time when the check was performed. */
  protected checkedAt = signal('');

  ngOnInit(): void {
    const token = this.route.snapshot.paramMap.get('token');
    if (token) {
      this.hasToken.set(true);
      this.verifyToken(token);
    }
    // No token → show manual entry form; loading stays false
  }

  protected submitManual(): void {
    const token = this.manualToken().trim();
    if (!token) return;
    this.hasToken.set(true);
    this.verifyToken(token);
  }

  private verifyToken(token: string): void {
    this.loading.set(true);
    this.error.set(null);
    this.result.set(null);

    this.api.verifyLicence(token).subscribe({
      next: (res) => {
        this.result.set(res);
        this.checkedAt.set(new Date().toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }));
        this.loading.set(false);
      },
      error: (err) => {
        if (err.status === 404) {
          this.error.set('Licence not found. Check the number and try again.');
        } else {
          this.error.set('An error occurred while verifying the licence. Please try again.');
        }
        this.loading.set(false);
      },
    });
  }
}
