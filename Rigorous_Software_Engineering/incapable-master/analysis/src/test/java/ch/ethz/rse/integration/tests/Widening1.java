
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE UNSAFE

public class Widening1 {

  public static void m1() {
    Store s = new Store(100, 100);
    int x = 0;
    for (int i = 0; i < 100; i++) {
        x++;
    }
    s.get_delivery(x);
  }
}
