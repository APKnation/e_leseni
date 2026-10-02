import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/api.service';

@Component({
  imports: [CommonModule],
  selector: 'app-verify',
  templateUrl: './verify.html',
})
export class Verify implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ApiService);

  protected loading = signal(true);
  protected error = signal<string | null>(null);
  protected result = signal<any>(null);

  ngOnInit(): void {
    const token = this.route.snapshot.paramMap.get('token');
    if (!token) {
      this.error.set('No token provided.');
      this.loading.set(false);
      return;
    }

    this.api.verifyLicence(token).subscribe({
      next: (res) => {
        this.result.set(res);
        this.loading.set(false);
      },
      error: (err) => {
        if (err.status === 404) {
          this.error.set('Licence not found or invalid QR code.');
        } else {
          this.error.set('An error occurred while verifying the licence.');
        }
        this.loading.set(false);
      },
    });
  }
}
