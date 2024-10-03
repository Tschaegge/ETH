
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE UNSAFE

public class Basic_Negative_Test {
  public static void m1(){
   Store s = new Store(-1,-1);
   s.get_delivery(0);
  }
 }