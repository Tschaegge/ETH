package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class FitsInTrolley_Test_For {

  public static void m1() {
    Store s = new Store(2, 4);
    int x = 0;
    for (int i = 0; i < 4; i++) {
        x++;
    }
    
    s.get_delivery(x);
  }
}
