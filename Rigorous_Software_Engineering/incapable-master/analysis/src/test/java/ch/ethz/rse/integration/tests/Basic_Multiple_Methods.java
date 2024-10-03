
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE SAFE

public class Basic_Multiple_Methods {

  public static void m1() {
    int a = 2;
    Store s = new Store(2, 4);
    s.get_delivery(a);
  }
  
  public static void m2() {
    int a = 2;
    Store s = new Store(2, 4);
    s.get_delivery(a);
    s.get_delivery(2);
  }
}