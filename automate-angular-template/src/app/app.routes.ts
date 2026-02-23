import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'examples/ui-components',
  },
  {
    path: 'examples/ui-components',
    loadComponent: () =>
      import('./examples/ui-components-gallery/ui-components-gallery.page').then(
        (m) => m.UiComponentsGalleryPage,
      ),
  },
  {
    path: '**',
    redirectTo: 'examples/ui-components',
  },
];
