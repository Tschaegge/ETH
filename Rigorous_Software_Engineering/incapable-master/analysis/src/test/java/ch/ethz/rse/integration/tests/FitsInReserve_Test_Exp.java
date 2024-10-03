package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE UNSAFE

public class FitsInReserve_Test_Exp {

  public static void m1() {
    Store s = new Store(4, 3);
    s.get_delivery(2*2);

  }
}
