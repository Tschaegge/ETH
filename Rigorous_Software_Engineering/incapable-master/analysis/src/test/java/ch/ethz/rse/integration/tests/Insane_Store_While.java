
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE UNSAFE

public class Insane_Store_While {
  public static void m1(int j){
    Store s = new Store(2, 4);
    int i = 0;
    while(i < j){
      s.get_delivery(1);
      i++;
    }
    
   }
 }

