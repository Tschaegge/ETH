package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE UNSAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE SAFE

public class NonNegative_Test_For1 {

  public static void m1() {
    Store s = new Store(2, 10);
    for (int i = 0; i < 10; i++) {
        s.get_delivery(-1);
    }
  }
}