package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE UNSAFE

public class FitsInReserve_Test_Basic {

  public static void m1() {
    Store s = new Store(2, 4);
    s.get_delivery(2);
    s.get_delivery(2);
    s.get_delivery(2);
    Store s2 = new Store(15, 20);
    s2.get_delivery(10);
    s2.get_delivery(10);
  }
}
