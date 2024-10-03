package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE UNSAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE SAFE

public class NonNegative_Test_Exp {

  public static void m1() {
    Store s = new Store(2, 4);
    int x = 2*(-1);
    s.get_delivery(x);
    s.get_delivery(2);    
  }
}
