package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class FitsInTrolley_Test_Exp {

  public static void m1() {
    Store s = new Store(2, 4);
    s.get_delivery(2*2-1);
    s.get_delivery(1-1+1);
  }
}