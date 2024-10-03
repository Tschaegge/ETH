package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class Basic_IF_TestGE {

  public static void m1() {
    Store s = new Store(2, 4);
    int a = 1;
    //a = a + 0;
    // TODO something goes wrong in the else statment -> probably need to implement widening first
    if(a>=2){
      s.get_delivery(2);
    } else {
      s.get_delivery(3);}
  }
}