package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class FitsInTrolley_Test_For1 {

  public static void m1() {
    Store s = new Store(2, 100);
    for (int i = 0; i < 4; i++) {
        s.get_delivery(4);
    }
  }
}
