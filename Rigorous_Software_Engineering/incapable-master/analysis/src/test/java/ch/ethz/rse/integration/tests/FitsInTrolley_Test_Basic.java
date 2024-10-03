package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class FitsInTrolley_Test_Basic {

  public static void m1() {
    Store s = new Store(2, 10);
    s.get_delivery(1);
    s.get_delivery(2);
    s.get_delivery(3);
    Store s2 = new Store(10, 20);
    s2.get_delivery(20);
  }
}